# Roadmap

Where gripsack is going. The north star: *a misconfiguration in any
file gripsack touches should produce the same quality of error as a
typo in a module.*

## Shipped

- The core flow: `apply` / `plan` / `generations` / `rollback` —
  generations on disk, atomic flip, no-op satisfaction
- Python frontend (typed, doctest-enforced)
- Fetchers: `github_release` (with resolution + `{version}`
  substitution), `git`, `brew` (bottles, with the pour), `pixi`,
  bare binaries / `.tar.xz` / `.zip`
- `gripfetch-*` plugin fetchers — NDJSON over stdio, every byte
  hash-verified by the core
- `grip update [MODULE]` — the flake cycle, per-module
- `--repo` bootstrap (path or git URL), eval provisioning via uv
- `tree(...)` — directory-shaped config deploys
- Foreign-path refusal: gripsack never touches a path it didn't deploy
  unless you say `--take-over`
- Prune-on-undeclare: remove a module from your repo and its deployed
  files go with it
- Per-host selection via auto-detected facts (os, arch, libc) and
  declared tags
- `verify` checks on deployed files
- Corporate proxy support, trusting the system CA roots
- `GRIPSACK_PYTHON` — the bring-your-own-interpreter escape hatch
- Run logs with causal spans; the debug and adopt skills

## Next

- TypeScript frontend
- `merge` + `template` ownership modes
- Exported env — modules contributing PATH and variables to your shell
- Activation adapters (`SystemdUser` first)
- Parallel scheduler with resource locks (the DAG is ready; execution
  is sequential today)
- `gc`, `why-owns`

## North star

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Config linters** (`griplint-*` plugins): validators for any
  dotfile format, same protocol as fetchers.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.
