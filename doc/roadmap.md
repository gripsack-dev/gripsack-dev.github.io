# Roadmap

Where gripsack is going. The north star: *a misconfiguration in any
file gripsack touches should produce the same quality of error as a
typo in a module.*

## Shipped

- The core flow: `apply` / `plan` / `generations` / `rollback` —
  generations on disk, atomic flip, no-op satisfaction
- Run-level rollback: a failed apply flips back or never happened — no
  half-applied deployments
- `grip check` — eval + sema + linters, exit code = validity, zero
  side effects; the CI gate for your dotfiles repo
- Python frontend (typed, doctest-enforced)
- Fetchers: `github_release` (with resolution + `{version}`
  substitution), `git`, `brew` (bottles, with the pour), `pixi`,
  bare binaries / `.tar.xz` / `.zip`
- `gripfetch-*` plugin fetchers — NDJSON over stdio, every byte
  hash-verified by the core
- Plugin protocol hardening: the locked pin travels in every request,
  provenance lands in the run log, stderr drains concurrently, and a
  600s deadline means no hangs
- `grip update [MODULE]` — the flake cycle, per-module
- `--repo` bootstrap (path or git URL), eval provisioning via uv —
  with self-contained bundled pixi *and* uv, per-platform pinned and
  sha256-verified
- `tree(...)` — directory-shaped config deploys
- Foreign-path refusal: gripsack never touches a path it didn't deploy
  unless you say `--take-over`
- Prune-on-undeclare: remove a module from your repo and its deployed
  files go with it
- E110 (missing source) + E111 (duplicate destination) — the plan-time
  gates for the two classic dotfile accidents
- Per-host selection via auto-detected facts (os, arch, libc) and
  declared tags
- `verify` checks on deployed files
- Parallel scheduler — N = cores, per-step resource flocks
- Lifecycle locks: `apply` / `gc` / `update` / `rollback` serialize,
  never interleave
- `gc` (+ `--dry-run`) and `why-owns`
- Exported env: `profile.sh` written at activation, plus `[eval] env`
  build-time injection
- Activation adapters (`SystemdUser` first)
- 22 config linters — `griplint-*` for the tools your dotfiles
  actually configure (helix, yazi, starship, zed, claude-code, …),
  as data packs in `crates/griplint`, with a weekly upstream-watch
  that files freshness issues; see [linters](linters.md)
- Corporate proxy support, trusting the system CA roots, `NO_PROXY`
  honored
- `GRIPSACK_PYTHON` — the bring-your-own-interpreter escape hatch
- Per-platform release matrix (linux + macOS, x86_64 + aarch64 — no
  Windows; WSL is the story), a homebrew cask, and a multi-platform
  install.sh, with a brew `version=` tripwire
- Run logs with causal spans; the debug and adopt skills
- `merge` + `template` ownership modes — a managed block inside
  foreign files (`.bashrc`), and payloads rendered from `{{ vars }}`
  at deploy time
- `grip init` — scaffold an env repo from the embedded template
- `[throttle]` token buckets + the `capabilities` op — rate budgets
  live in fetchers; `[throttle]` in env.toml outranks them, and
  buckets persist across runs

## Next

- TypeScript frontend
- Fetcher `package =` provisioning (the linter story, for transports)
- Fonts and desktop-entry activation adapters
- Module env inheritance for dependents

## North star

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.
- **griplint engine in-crate**: the data packs run in-process — no
  plugin lifecycle for first-party linters (plan/0012 move 3). (This
  replaces the old "griplint-ts" idea — with linters as data there is
  nothing to mirror.)
