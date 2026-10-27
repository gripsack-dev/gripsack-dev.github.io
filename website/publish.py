#!/usr/bin/env python3
"""Commit locally rendered public/ and dispatch one upload-only Pages job."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
REPOSITORY = "gripsack-dev/gripsack-dev.github.io"
REMOTE = f"https://github.com/{REPOSITORY}.git"
BRANCH = "published-site"


def git(directory, *arguments):
    return subprocess.check_output(["git", "-C", str(directory), *arguments], text=True).strip()


def main():
    for name in ("index.html", "CNAME"):
        if not (PUBLIC / name).is_file():
            raise SystemExit("Build public/ with website/build.py before publishing")
    for path in PUBLIC.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise SystemExit(f"Static publication contains a link or special file: {path}")

    exists = subprocess.run(["git", "ls-remote", "--exit-code", "--heads", REMOTE, BRANCH],
                            capture_output=True, text=True)
    if exists.returncode not in (0, 2):
        raise SystemExit(exists.stderr)
    with tempfile.TemporaryDirectory(prefix="gripsack-site-publish-") as temporary:
        staging = Path(temporary) / "site"
        if exists.returncode == 0:
            subprocess.run(["git", "clone", "--depth", "1", "--branch", BRANCH, REMOTE, str(staging)], check=True)
            # Only this disposable checkout is cleared; history and .git stay.
            for path in staging.iterdir():
                if path.name == ".git":
                    continue
                if path.is_symlink() or path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
        else:
            staging.mkdir()
            git(staging, "init", "-b", BRANCH)
            git(staging, "remote", "add", "origin", REMOTE)
        for key in ("user.name", "user.email"):
            identity = subprocess.run(["git", "-C", str(ROOT), "config", "--get", key],
                                      capture_output=True, text=True)
            if identity.returncode == 0:
                git(staging, "config", key, identity.stdout.strip())
        shutil.copytree(PUBLIC, staging, dirs_exist_ok=True)
        (staging / ".nojekyll").touch()
        git(staging, "add", "--all")
        changed = subprocess.run(["git", "-C", str(staging), "diff", "--cached", "--quiet"])
        if changed.returncode == 1:
            git(staging, "commit", "-m", "Publish locally rendered website")
        elif changed.returncode != 0:
            raise SystemExit(changed.returncode)
        commit = git(staging, "rev-parse", "HEAD")
        # No force push: concurrent publication must be reconciled, not erased.
        git(staging, "push", "origin", f"HEAD:refs/heads/{BRANCH}")
    subprocess.run(["gh", "workflow", "run", "pages.yml", "--repo", REPOSITORY,
                    "--ref", "main", "-f", f"site_commit={commit}"], check=True)
    print(f"Dispatched static publication for {commit}; no product build or signing.")


if __name__ == "__main__":
    main()
