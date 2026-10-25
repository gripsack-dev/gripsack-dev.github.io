#!/usr/bin/env python3
"""Assemble the gripsack website into public/.

Single source of truth: the landing page is website/index.html, and the
docs pages are converted from doc/*.md at build time — editing a doc in
the repo is all it takes to update the site (pages.yml redeploys).
Every docs page shares one chrome: a left rail (brand, site nav,
on-this-page TOC) and a content column.

    uv run --with markdown python website/build.py --release-tag "$TAG" \
      --manifest-sha256 "$MANIFEST_SHA256" --run-id "$SIGNING_RUN_ID"
"""

from __future__ import annotations

import hashlib
import re
import shutil
import json
from pathlib import Path

import markdown
import release

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"

# The palette picker's set (website/index.html data-set-palette) — demo
# variants are stamped only for these.
PALETTES = {
    "catppuccin-mocha",
    "catppuccin-latte",
    "tokyo-night",
    "gruvbox-dark",
    "nord",
    "dracula",
    "one-dark",
    "one-light",
    "github-light",
    "solarized-dark",
    "solarized-light",
}

REPO = "https://github.com/gripsack-dev/gripsack"

# Cache-busting: content hash of the shared assets, stamped into every
# css/js URL as ?v=…
_ASSET_VERSION: str | None = None




def site_version() -> str:
    """All rendered current-version data comes from the admitted release."""
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
    # fetched from the app repo at build time — the changelog lives with
    # the code (fetch failure falls back to the last committed copy)
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
    for slug, (src, _) in PAGES.items():
        root = "../" * (1 + slug.count("/"))
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
        dst = OUT / "docs" / f"{slug}.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            page(f"gripsack — {title.lower()}", body, f"docs/{slug}.html", toc, root)
        )
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
    index = index.replace("./assets/site.css", f"./assets/site.css?v={asset_version()}")
    index = index.replace("./assets/site.js", f"./assets/site.js?v={asset_version()}")
    # Stamp the demo variants that actually shipped into every demo img, so
    # site.js never guesses a missing variant (and never 404s). Each slide's
    # base gets its own list: <base>-<palette>.gif on disk = available.
    def stamp_demo_variants(m: re.Match) -> str:
        tag = m.group(0)
        stem = Path(m.group(1)).name
        if not (ROOT / "img" / f"{stem}.gif").exists():
            # the slide's own GIF hasn't shipped yet — fall back to the
            # default demo (palette variants included) instead of 404ing
            tag = tag.replace(f'src="./img/{stem}.gif"', 'src="./img/demo.gif"')
            tag = tag.replace(
                f'data-demo-base="./img/{stem}"', 'data-demo-base="./img/demo"'
            )
            stem = "demo"
        # filter to real palette names — demo-init-*.gif etc. would
        # otherwise pollute the base demo's list ("init-nord", …)
        variants = ",".join(
            sorted(
                v
                for p in (ROOT / "img").glob(f"{stem}-*.gif")
                if (v := p.stem.removeprefix(f"{stem}-")) in PALETTES
            )
        )
        return tag.replace('data-demo-variants=""', f'data-demo-variants="{variants}"')

    index = re.sub(
        r'<img[^>]*data-demo-base="([^"]+)"[^>]*>', stamp_demo_variants, index
    )
    (OUT / "index.html").write_text(index)
    # Custom domain — GitHub Pages reads this from the deployed artifact.
    (OUT / "CNAME").write_text("gripsack.dev\n")
    # flat URLs that moved into folders — redirect stubs
    for flat, nested in (
        ("apt", "fetchers/apt"),
        ("settings-reference", "settings/reference"),
    ):
        (OUT / "docs" / f"{flat}.html").write_text(
            '<!DOCTYPE html><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url=./{nested}.html">'
            f'<link rel="canonical" href="./{nested}.html">'
        )
    # Exact Git blob bytes from the authenticated source, not mutable main.
    (OUT / "install.sh").write_bytes(RELEASE_FILES["install.sh"])
    (OUT / "release.json").write_text(json.dumps(RELEASE, sort_keys=True) + "\n")
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("icon.svg", "favicon.svg", "site.css", "site.js"):
        shutil.copy(ROOT / "website" / "assets" / name, OUT / "assets" / name)
    shutil.copy(ROOT / "doc" / "logo.svg", OUT / "assets" / "logo.svg")
    (OUT / "img").mkdir(exist_ok=True)
    for gif in (ROOT / "img").glob("*.gif"):
        shutil.copy(gif, OUT / "img" / gif.name)
    # the PEP 503 index for griplint-* packages, served at /simple —
    # and mirrored at /packages: some content-filtering egress blocks
    # /simple/* paths specifically (observed: Bloomberg's proxy)
    if (ROOT / "simple").exists():
        shutil.copytree(ROOT / "simple", OUT / "simple", dirs_exist_ok=True)
        shutil.copytree(ROOT / "simple", OUT / "packages", dirs_exist_ok=True)
    # Stamp the demo variants that actually shipped into the img tag, so
    # site.js never guesses a missing variant (and never 404s).
    for name in DOC_ASSETS:
        shutil.copy(ROOT / "doc" / name, OUT / "assets" / name)
    print("copied landing page + assets")


if __name__ == "__main__":
    # Complete admission and source downloads BEFORE touching existing output.
    RELEASE, RELEASE_FILES = release.admit(*release.selected_inputs(release.arguments()))
    assemble()
    build_docs()
