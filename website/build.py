#!/usr/bin/env python3
"""Build static pages locally from the site tree and a selected core Git commit.

    uv run --with markdown python website/build.py --core ../gripsack --core-ref core-v0.48.0
    python3 -m http.server 8000 --directory public
    python3 website/publish.py

The core version, changelog and existing installer are read from local Git
objects. This is documentation rendering, not signature or release admission.
Pages only uploads/deploys the resulting static commit; it never builds products.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import json
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


# Docs mirrored onto the site: url-slug -> (source file, nav label).
PAGES: dict[str, tuple[str, str]] = {
    "adopting": ("doc/adopting.md", "adopting your dotfiles"),
    "compare": ("doc/compare.md", "compare"),
    "architecture": ("doc/architecture.md", "architecture"),
    "safety": ("doc/safety.md", "safety"),
    "modules": ("doc/modules.md", "modules"),
    "environments": ("doc/environments.md", "environments"),
    "workspace-migration": ("doc/workspace-migration.md", "workspace migration"),
    "settings": ("doc/settings.md", "settings"),
    "settings/reference": ("doc/settings/reference.md", "settings reference"),
    "runs": ("doc/runs.md", "run logs"),
    "fetchers": ("doc/fetchers.md", "fetchers"),
    "fetchers/apt": ("doc/fetchers/apt.md", "apt"),
    "linters": ("doc/linters.md", "linters"),
    "skills": ("doc/skills.md", "skills"),
    "roadmap": ("doc/roadmap.md", "roadmap"),
    # The changelog remains with the selected core source, not a second mirror.
    "changelog": ("doc/changelog.md", "what's new"),
}

# Links inside the mirrored docs that point at files we do NOT mirror:
# send them to the blob/tree on GitHub instead.
GITHUB_LINKS: dict[str, str] = {
    "../plan/": f"{REPO}/tree/main/plan/",
    "plan/": f"{REPO}/tree/main/plan/",
}

# Doc-local SVG diagrams: inlined and re-themed alongside the logo.
DOC_ASSETS = {"architecture.svg", "linters-flow.svg", "fetchers-flow.svg"}

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
    # nested slugs (fetchers/apt) render indented under their parent
    links = "".join(
        f'    <a{" class=\"active child\"" if href == active else ""}'
        f'{" class=\"child\"" if href != active else ""}'
        f' href="{root}{href}">{"↳ " if href.count("/") > 1 else ""}{label}</a>\n'
        if href.count("/") > 1
        else f'    <a{" class=\"active\"" if href == active else ""} href="{root}{href}">{label}</a>\n'
        for href, label in RAIL_LINKS
    )
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
  <nav>
{links}    <a class="gh" href="{REPO}">github ↗</a>
    <a href="{root}docs/roadmap.html#supported-platforms">Linux &amp; WSL support</a>
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
<meta name="description" content="gripsack for Linux and WSL — your whole environment in one bag. Packages from any source plus your dotfiles, with generations and rollback.">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css?v={asset_version()}">
<script src="{root}assets/site.js?v={asset_version()}" defer></script>
</head>
<body class="docs">
<div class="shell">
{rail(active, toc, root)}
<main class="content">
<article class="md">
<p class="note">Documentation for core/SDK v{site_version()}.
<a href="{root}docs/roadmap.html#release-qualification">Release and verification scope</a>.</p>
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
    """Fix links/images in converted doc HTML for their new home."""
    for name in DOC_ASSETS:
        body = body.replace(f'src="{name}"', f'src="{root}assets/{name}"')
    for slug in slugs:
        # `slug.md` and `slug.md#anchor` both land on the built page;
        # anchors previously survived un-rewritten and 404'd.
        body = re.sub(
            rf'href="{re.escape(slug)}\.md(#[^"]*)?"',
            lambda m: f'href="{root}docs/{slug}.html{m.group(1) or ""}"',
            body,
        )
    for src, dst in GITHUB_LINKS.items():
        body = body.replace(f'href="{src}', f'href="{dst}')
    return body




def build_docs() -> None:
    slugs = set(PAGES)
    destinations = {slug: slug for slug in PAGES}
    destinations.update({"apt": "fetchers/apt", "settings-reference": "settings/reference"})
    for destination, slug in destinations.items():
        src, _ = PAGES[slug]
        root = "../" * (1 + destination.count("/"))
        path = ROOT / src
        if slug == "changelog":
            text = RELEASE_FILES["CHANGELOG.md"].decode("utf-8")
        else:
            text = path.read_text()
        text = text.replace("{release_source}", RELEASE["source"]["commit"])
        body = markdown.markdown(
            text, extensions=["fenced_code", "tables", "toc", "sane_lists"]
        )
        body = rewrite(body, slugs, root)
        # Inline + theme doc-local SVG diagrams.
        for name in DOC_ASSETS:
            if name.endswith(".svg"):

                def inline_svg(m: re.Match, name: str = name) -> str:
                    alt = re.search(r'alt="([^"]*)"', m.group(0))
                    label = alt.group(1) if alt else name
                    return (
                        f'<div class="diagram" role="img" aria-label="{label}">'
                        f"{themed_svg(ROOT / 'doc' / name)}</div>"
                    )

                body = re.sub(
                    rf'<img [^>]*src="\.\./assets/{re.escape(name)}"[^>]*>',
                    inline_svg,
                    body,
                )
        title = re.match(r"# (.+)", text).group(1).strip()
        toc = extract_toc(body)
        dst = OUT / "docs" / f"{destination}.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        rendered = page(f"gripsack — {title.lower()}", body, f"docs/{slug}.html", toc, root)
        if destination != slug:
            # Meta refresh drops fragments. Keep the full page usable without
            # JavaScript; normal navigation preserves queries and deep links.
            canonical = f"{root}docs/{slug}.html"
            redirect = (
                f'<link rel="canonical" href="{canonical}">'
                f'<script>location.replace({json.dumps(canonical)}'
                '+location.search+location.hash)</script>'
            )
            rendered = rendered.replace("</head>", redirect + "</head>")
        dst.write_text(rendered)
        print(f"built docs/{destination}.html from {src} ({len(toc)} toc entries)")


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
    # Historical media URLs remain valid, although the homepage no longer loads them.
    (OUT / "img").mkdir(exist_ok=True)
    for gif in (ROOT / "img").glob("*.gif"):
        shutil.copy(gif, OUT / "img" / gif.name)
    # the PEP 503 index for griplint-* packages, served at /simple —
    # and mirrored at /packages: some content-filtering egress blocks
    # /simple/* paths specifically (observed: Bloomberg's proxy)
    if (ROOT / "simple").exists():
        shutil.copytree(ROOT / "simple", OUT / "simple", dirs_exist_ok=True)
        shutil.copytree(ROOT / "simple", OUT / "packages", dirs_exist_ok=True)
    for name in DOC_ASSETS:
        shutil.copy(ROOT / "doc" / name, OUT / "assets" / name)
    print("copied landing page + assets")


def local_core_inputs(core: Path, reference: str) -> tuple[dict, dict[str, bytes]]:
    commit = subprocess.check_output(
        ["git", "-C", str(core), "rev-parse", "--verify", "--end-of-options",
         reference + "^{commit}"], text=True,
    ).strip()

    def blob(name: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(core), "show", f"{commit}:{name}"])

    manifest = tomllib.loads(blob("Cargo.toml").decode("utf-8"))
    files = {name: blob(name) for name in ("CHANGELOG.md", "install.sh")}
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
