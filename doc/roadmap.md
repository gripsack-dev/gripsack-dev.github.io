# Roadmap

Where gripsack is going. 0.2 is live; 1.0 is the north star — *a
misconfiguration in any file gripsack touches should produce the same
quality of error as a typo in a module.*

## Shipped — 0.1

- The core flow: `apply` / `plan` / `generations` / `rollback`
- `file` + `tarball` fetchers, `owned` + `tracked-copy` ownership
- Python frontend (typed, doctest-enforced), TypeScript frontend
- Generations on disk, atomic flip, no-op satisfaction
- Run logs with causal spans; the debug skill

## Shipped — 0.2

- Fetchers: `github_release` (with resolution + `{version}`
  substitution), `git`, `brew` (bottles, with the pour), `pixi`,
  bare binaries / `.tar.xz` / `.zip`
- `gripfetch-*` plugin protocol host — NDJSON, hash-verified
- `grip update [MODULE]` — the flake cycle, per-module
- `--repo` bootstrap (path or git URL), eval provisioning via uv
- `gripsack-adopt` skill — interview-driven migration
- E108/E109 plan-time gates for unimplemented modes and verify paths

## Next — 0.3

- TypeScript eval path
- Activation adapters (`SystemdUser` first), `merge` + `template`
  ownership modes
- Parallel scheduler with resource locks (the DAG is ready; execution
  is sequential today)
- `gc`, `why-owns`
- Tree entries (directory-shaped config deploys)
- External satisfaction (never touch a path gripsack didn't deploy)

## North star — 1.0

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Validator plugins** (`grip check`): validators for any dotfile
  format, same protocol as fetchers.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.
