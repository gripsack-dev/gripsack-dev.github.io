#!/usr/bin/env python3
"""Build static pages locally from the site tree and a selected core Git commit.

    uv run --with markdown python website/build.py --core ../gripsack --core-ref HEAD
    python3 -m http.server 8000 --directory public
    python3 website/publish.py

The core version and existing installer are read from local Git objects.
This is documentation rendering, not signature or release admission.
Pages only uploads/deploys the resulting static commit; it never builds products.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"


REPO = "https://github.com/gripsack-dev/gripsack"

# Cache-busting: content hash of the shared assets, stamped into every
# css/js URL as ?v=…
_ASSET_VERSION: str | None = None




def site_version() -> str:
    """Version of the explicitly selected local core source."""
    return RELEASE["version"]


def asset_version() -> str:
    global _ASSET_VERSION
    if _ASSET_VERSION is None:
        h = hashlib.sha1()
        for name in ("site.css", "site.js"):
            h.update((ROOT / "website" / "assets" / name).read_bytes())
        _ASSET_VERSION = h.hexdigest()[:8]
    return _ASSET_VERSION


# Canonical product docs: url-slug -> (source file, nav label).
PAGES: dict[str, tuple[str, str]] = {
    "install": ("doc/install.md", "install"),
    "workspaces": ("doc/workspaces.md", "workspaces"),
    "packages": ("doc/packages.md", "packages"),
    "environments": ("doc/environments.md", "environments"),
    "adopting": ("doc/adopting.md", "profiles & dotfiles"),
    "builds": ("doc/builds.md", "BuildKit & OCI"),
    "tasks": ("doc/tasks.md", "tasks & checks"),
    "fetchers": ("doc/fetchers.md", "sources & locks"),
    "safety": ("doc/safety.md", "safety & recovery"),
    "settings": ("doc/settings.md", "settings"),
    "settings/reference": ("doc/settings/reference.md", "settings reference"),
    "runs": ("doc/runs.md", "run logs"),
    "skills": ("doc/skills.md", "agent guidance"),
    "compare": ("doc/compare.md", "where it fits"),
    "architecture": ("doc/architecture.md", "architecture"),
    "changelog": ("doc/changelog.md", "what's new"),
}

# Palette hexes -> site CSS vars, so inlined SVGs re-theme with the
# palette picker (an <img> can't inherit page CSS).
LOGO_VARS = {
    "#11111b": "var(--bg)",
    "#1e1e2e": "var(--card)",
    "#181825": "var(--deep)",
    "#313244": "var(--border)",
    "#45475a": "color-mix(in srgb, var(--border) 55%, var(--border-strong))",
    "#585b70": "var(--border-strong)",
    "#6c7086": "var(--faint)",
    "#a6adc8": "var(--dim)",
    "#cdd6f4": "var(--text)",
    "#89b4fa": "var(--blue)",
    "#a6e3a1": "var(--green)",
    "#f9e2af": "var(--yellow)",
    "#fab387": "var(--peach)",
    "#f38ba8": "var(--red)",
    "#cba6f7": "var(--mauve)",
    "#94e2d5": "var(--teal)",
}


def themed_svg(path: Path) -> str:
    svg = path.read_text()
    for hex_color, var in LOGO_VARS.items():
        svg = svg.replace(hex_color, var)
    return svg.strip()


def themed_logo() -> str:
    svg = themed_svg(ROOT / "doc" / "logo.svg")
    # no tile on the site: the bag art themes with the palette and
    # grounds itself with a CSS drop-shadow that follows its
    # silhouette (.hero .logo svg). A backdrop rect — solid, radial,
    # or feathered — always left an edge to fight the spotlight.
    # (doc/logo.svg keeps the static bake for README/og: an <img>
    # there has no page to blend with.)
    tile = '<rect width="480" height="310" rx="18" fill="var(--bg)"/>'
    if tile in svg:
        svg = svg.replace(tile, "", 1)
    else:
        print("warning: logo tile rect not found — tile removal skipped")
    return svg


RAIL_LINKS = [("index.html", "home")] + [
    (f"docs/{slug}.html", label) for slug, (_, label) in PAGES.items()
]

PALETTE_DOTS = [
    ("catppuccin-mocha", "#89b4fa"),
    ("tokyo-night", "#7aa2f7"),
    ("gruvbox-dark", "#83a598"),
    ("nord", "#88c0d0"),
    ("dracula", "#bd93f9"),
    ("one-dark", "#61afef"),
    ("solarized-dark", "#268bd2"),
    ("catppuccin-latte", "#1e66f5"),
    ("github-light", "#0969da"),
    ("one-light", "#4078f2"),
    ("solarized-light", "#268bd2"),
]


def rail(active: str, toc: list[tuple[str, str]], root: str = "../") -> str:
    # Nested canonical pages render indented under their parent.
    entries = []
    for href, label in RAIL_LINKS:
        child = href.count("/") > 1
        classes = " ".join(name for name, enabled in (
            ("active", href == active), ("child", child),
        ) if enabled)
        current = ' aria-current="page"' if href == active else ""
        entries.append(
            f'    <a class="{classes}"{current} href="{root}{href}">'
            f'{"↳ " if child else ""}{html.escape(label)}</a>\n'
        )
    links = "".join(entries)
    toc_html = "".join(f'    <a href="#{anchor}">{label}</a>\n' for label, anchor in toc)
    toc_block = (
        f'  <span class="rail-head">on this page</span>\n  <div class="rail-toc">\n{toc_html}  </div>\n'
        if toc_html
        else ""
    )
    dots = "".join(
        f'    <button data-set-palette="{name}" title="{name}" '
        f'style="--sw:{color}" aria-label="{name}"></button>\n'
        for name, color in PALETTE_DOTS
    )
    return f"""<aside class="rail">
  <a class="brand" href="{root}index.html">
    <img src="{root}assets/icon.svg" alt="gripsack icon"><span class="wordmark">gripsack</span>
  </a>
  <span class="rail-head">menu</span>
  <nav aria-label="Documentation">
{links}    <a class="gh" href="{REPO}">github ↗</a>
  </nav>
{toc_block}  <span class="rail-head">theme</span>
  <div class="rail-palettes">
{dots}  </div>
  <span class="palette-name" data-palette-name>catppuccin-mocha</span>
</aside>"""


def page(title: str, body: str, active: str, toc: list[tuple[str, str]], root: str = "../") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Declare user-space packages, native environments and personal profiles. Build with BuildKit, export OCI images and retain managed generations.">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css?v={asset_version()}">
<script src="{root}assets/site.js?v={asset_version()}" defer></script>
</head>
<body class="docs">
<a class="skip-link" href="#main">Skip to content</a>
<div class="shell">
{rail(active, toc, root)}
<main class="content" id="main">
<article class="md">
{body}
</article>
<footer>
  <span><span class="blink"></span> © 2026 <a href="https://github.com/tknawara">Tarek Nawara</a></span>
  <span>MIT license</span>
  <a href="https://github.com/gripsack-dev">gripsack-dev</a>
  <a href="{REPO}">source</a>
  <a href="{root}index.html">home</a>
  <span style="margin-left:auto"><span class="fversion">v{site_version()}</span> · eleven palettes</span>
</footer>
</main>
</div>
</body>
</html>
"""


def extract_toc(md_body: str) -> list[tuple[str, str]]:
    toc = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', md_body):
        label = re.sub(r"<[^>]+>", "", m.group(2))
        toc.append((label, m.group(1)))
    return toc


def rewrite(body: str, slugs: set[str], root: str = "../") -> str:
    """Resolve canonical doc links from any page depth."""
    for slug in slugs:
        # `slug.md` and `slug.md#anchor` both land on the built page;
        # anchors previously survived un-rewritten and 404'd.
        body = re.sub(
            rf'href="{re.escape(slug)}\.md(#[^"]*)?"',
            lambda m: f'href="{root}docs/{slug}.html{m.group(1) or ""}"',
            body,
        )
    return body




def build_docs() -> None:
    slugs = set(PAGES)
    for slug, (src, _) in PAGES.items():
        root = "../" * (1 + slug.count("/"))
        text = (ROOT / src).read_text()
        text = text.replace("{release_source}", RELEASE["source"]["commit"])
        text = text.replace("{core_version}", site_version())
        body = markdown.markdown(
            text, extensions=["fenced_code", "tables", "toc", "sane_lists"]
        )
        body = rewrite(body, slugs, root)
        title = re.match(r"# (.+)", text).group(1).strip()
        toc = extract_toc(body)
        dst = OUT / "docs" / f"{slug}.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page(f"gripsack — {title.lower()}", body, f"docs/{slug}.html", toc, root))
        print(f"built docs/{slug}.html from {src} ({len(toc)} toc entries)")


def assemble() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "docs").mkdir(parents=True)

    index = (ROOT / "website" / "index.html").read_text()
    assert "<!--LOGO-->" in index, "index.html lost its <!--LOGO--> placeholder"
    index = index.replace("<!--LOGO-->", themed_logo())
    index = index.replace("<!--VERSION-->", site_version())
    index = index.replace("{version}", site_version())
    index = index.replace("{release_source}", RELEASE["source"]["commit"])
    index = index.replace("./assets/site.css", f"./assets/site.css?v={asset_version()}")
    index = index.replace("./assets/site.js", f"./assets/site.js?v={asset_version()}")
    (OUT / "index.html").write_text(index)
    # Custom domain — GitHub Pages reads this from the deployed artifact.
    (OUT / "CNAME").write_text("gripsack.dev\n")
    # Preserve the installer endpoint without bypassing its own checks.
    (OUT / "install.sh").write_bytes(RELEASE_FILES["install.sh"])
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("icon.svg", "favicon.svg", "site.css", "site.js"):
        shutil.copy(ROOT / "website" / "assets" / name, OUT / "assets" / name)
    shutil.copy(ROOT / "doc" / "logo.svg", OUT / "assets" / "logo.svg")
    # Independently supported griplint distribution endpoints stay outside
    # product navigation; /packages also serves clients that block /simple.
    if (ROOT / "simple").exists():
        shutil.copytree(ROOT / "simple", OUT / "simple", dirs_exist_ok=True)
        shutil.copytree(ROOT / "simple", OUT / "packages", dirs_exist_ok=True)
    print("copied landing page + assets")


def local_core_inputs(core: Path, reference: str) -> tuple[dict, dict[str, bytes]]:
    commit = subprocess.check_output(
        ["git", "-C", str(core), "rev-parse", "--verify", "--end-of-options",
         reference + "^{commit}"], text=True,
    ).strip()

    def blob(name: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(core), "show", f"{commit}:{name}"])

    manifest = tomllib.loads(blob("Cargo.toml").decode("utf-8"))
    files = {"install.sh": blob("install.sh")}
    return {"version": manifest["workspace"]["package"]["version"],
            "source": {"commit": commit}}, files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True, help="local core Git repository")
    parser.add_argument("--core-ref", default="HEAD", help="core commit or tag to document")
    args = parser.parse_args()
    # Resolve every input before replacing generated output.
    RELEASE, RELEASE_FILES = local_core_inputs(args.core.resolve(), args.core_ref)
    print(f"documenting core {RELEASE['version']} at {RELEASE['source']['commit']}")
    assemble()
    build_docs()
