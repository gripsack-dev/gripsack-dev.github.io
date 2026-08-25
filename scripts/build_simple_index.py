#!/usr/bin/env python3
"""Build a PEP 503 simple index from a directory of wheels/sdists.

Usage: build_simple_index.py <wheels_dir> <index_out_dir>

Layout produced (GitHub Pages–servable, no redirects):

    simple/index.html                 package list
    simple/<normalized-name>/index.html   artifact links
    simple/<normalized-name>/<file>   the artifacts

Normalization per PEP 503: lowercase, runs of -_. → -.
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

ARTIFACT_SUFFIXES = (".whl", ".tar.gz", ".zip")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


def package_name(filename: str) -> str:
    """griplint_helix-0.1.1-py3-none-any.whl → griplint-helix"""
    stem = re.split(r"-\d", filename, maxsplit=1)[0]
    return normalize(stem.replace("_", "-"))


def main(wheels_dir: Path, out_dir: Path) -> None:
    artifacts: dict[str, list[Path]] = {}
    for path in sorted(wheels_dir.iterdir()):
        if path.suffix in ARTIFACT_SUFFIXES or path.name.endswith(".tar.gz"):
            if path.name.endswith(".sha256"):
                continue
            artifacts.setdefault(package_name(path.name), []).append(path)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    index_links = []
    for name, files in sorted(artifacts.items()):
        pkg_dir = out_dir / name
        pkg_dir.mkdir()
        links = []
        for f in files:
            shutil.copy2(f, pkg_dir / f.name)
            sha = (f.parent / f"{f.name}.sha256")
            if sha.exists():
                shutil.copy2(sha, pkg_dir / sha.name)
                links.append(
                    f'    <a href="{f.name}#sha256={sha.read_text().split()[0]}">{html.escape(f.name)}</a><br/>'
                )
            else:
                links.append(f'    <a href="{f.name}">{html.escape(f.name)}</a><br/>')
        (pkg_dir / "index.html").write_text(
            "<!DOCTYPE html>\n<html>\n  <head><title>Links for "
            f"{html.escape(name)}</title></head>\n  <body>\n"
            f"    <h1>Links for {html.escape(name)}</h1>\n" + "\n".join(links) + "\n  </body>\n</html>\n"
        )
        index_links.append(f'    <a href="{name}/">{html.escape(name)}</a><br/>')

    (out_dir / "index.html").write_text(
        "<!DOCTYPE html>\n<html>\n  <head><title>Simple index</title></head>\n  <body>\n"
        + "\n".join(index_links)
        + "\n  </body>\n</html>\n"
    )
    print(f"indexed {sum(len(v) for v in artifacts.values())} artifacts "
          f"across {len(artifacts)} packages → {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: build_simple_index.py <wheels_dir> <index_out_dir>")
        raise SystemExit(2)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
