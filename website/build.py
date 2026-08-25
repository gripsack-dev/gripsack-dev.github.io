#!/usr/bin/env python3
"""Assemble the gripsack website into public/.

Single source of truth: the landing page is website/index.html, and the
docs pages are converted from doc/*.md at build time — editing a doc in
the repo is all it takes to update the site (pages.yml redeploys).
Every docs page shares one chrome: a left rail (brand, site nav,
on-this-page TOC) and a content column.

    uv run --with markdown python website/build.py    # → public/
"""

from __future__ import annotations

import hashlib
import re
import shutil
import urllib.request
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"

REPO = "https://github.com/gripsack-dev/gripsack"

# Cache-busting: content hash of the shared assets, stamped into every
# css/js URL as ?v=…
_ASSET_VERSION: str | None = None


def latest_release() -> str:
    """The current release tag, fetched at build time; stale-safe fallback."""
    try:
        with urllib.request.urlopen(
            "https://api.github.com/repos/gripsack-dev/gripsack/releases/latest"
        ) as r:
            import json

            return json.load(r)["tag_name"].removeprefix("core-v")
    except Exception:
        return "0.4.1"


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
    "architecture": ("doc/architecture.md", "architecture"),
    "modules": ("doc/modules.md", "modules"),
    "settings": ("doc/settings.md", "settings"),
    "settings-reference": ("doc/settings-reference.md", "settings reference"),
    "runs": ("doc/runs.md", "run logs"),
    "fetchers": ("doc/fetchers.md", "fetchers"),
    "linters": ("doc/linters.md", "linters"),
    "skills": ("doc/skills.md", "skills"),
    "roadmap": ("doc/roadmap.md", "roadmap"),
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
    return themed_svg(ROOT / "doc" / "logo.svg")


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


def rail(active: str, toc: list[tuple[str, str]]) -> str:
    links = "".join(
        f'    <a{" class=\"active\"" if href == active else ""} href="../{href}">{label}</a>\n'
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
  <a class="brand" href="../index.html">
    <img src="../assets/icon.svg" alt="gripsack icon"><span class="wordmark">gripsack</span>
  </a>
  <span class="rail-head">menu</span>
  <nav>
{links}    <a class="gh" href="{REPO}">github ↗</a>
  </nav>
{toc_block}  <span class="rail-head">theme</span>
  <div class="rail-palettes">
{dots}  </div>
  <span class="palette-name" data-palette-name>catppuccin-mocha</span>
</aside>"""


def page(title: str, body: str, active: str, toc: list[tuple[str, str]]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="gripsack — your whole environment in one bag. Packages from any source plus your dotfiles, with generations and rollback.">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/site.css?v={asset_version()}">
<script src="../assets/site.js?v={asset_version()}" defer></script>
</head>
<body class="docs">
<div class="shell">
{rail(active, toc)}
<main class="content">
<article class="md">
{body}
</article>
<footer>
  <span>MIT license</span>
  <a href="{REPO}">source</a>
  <a href="../index.html">home</a>
  <span style="margin-left:auto">a gripsack-dev project · eleven palettes</span>
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


def rewrite(body: str, slugs: set[str]) -> str:
    """Fix links/images in converted doc HTML for their new home."""
    for name in DOC_ASSETS:
        body = body.replace(f'src="{name}"', f'src="../assets/{name}"')
    for slug in slugs:
        body = body.replace(f'href="{slug}.md"', f'href="./{slug}.html"')
    for src, dst in GITHUB_LINKS.items():
        body = body.replace(f'href="{src}', f'href="{dst}')
    return body


def build_docs() -> None:
    slugs = set(PAGES)
    for slug, (src, _) in PAGES.items():
        text = (ROOT / src).read_text()
        body = markdown.markdown(
            text, extensions=["fenced_code", "tables", "toc", "sane_lists"]
        )
        body = rewrite(body, slugs)
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
            page(f"gripsack — {title.lower()}", body, f"docs/{slug}.html", toc)
        )
        print(f"built docs/{slug}.html from {src} ({len(toc)} toc entries)")


def assemble() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "docs").mkdir(parents=True)

    index = (ROOT / "website" / "index.html").read_text()
    assert "<!--LOGO-->" in index, "index.html lost its <!--LOGO--> placeholder"
    index = index.replace("<!--LOGO-->", themed_logo())
    index = index.replace("<!--VERSION-->", latest_release())
    index = index.replace("./assets/site.css", f"./assets/site.css?v={asset_version()}")
    index = index.replace("./assets/site.js", f"./assets/site.js?v={asset_version()}")
    (OUT / "index.html").write_text(index)
    # Custom domain — GitHub Pages reads this from the deployed artifact.
    (OUT / "CNAME").write_text("gripsack.dev\n")
    # The installer, served at gripsack.dev/install.sh (source of truth:
    # the gripsack repo).
    installer = urllib.request.urlopen(
        "https://raw.githubusercontent.com/gripsack-dev/gripsack/main/install.sh"
    ).read()
    (OUT / "install.sh").write_bytes(installer)
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("icon.svg", "favicon.svg", "site.css", "site.js"):
        shutil.copy(ROOT / "website" / "assets" / name, OUT / "assets" / name)
    shutil.copy(ROOT / "doc" / "logo.svg", OUT / "assets" / "logo.svg")
    (OUT / "img").mkdir(exist_ok=True)
    shutil.copy(ROOT / "img" / "demo.gif", OUT / "img" / "demo.gif")
    for name in DOC_ASSETS:
        shutil.copy(ROOT / "doc" / name, OUT / "assets" / name)
    print("copied landing page + assets")


if __name__ == "__main__":
    assemble()
    build_docs()
