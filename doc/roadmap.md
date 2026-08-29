# Roadmap

Where gripsack is going. The north star: *a misconfiguration in any
file gripsack touches should produce the same quality of error as a
typo in a module.*

## Shipped

- The core flow: `apply` / `plan` / `generations` / `rollback` —
  generations on disk, atomic flip, no-op satisfaction
- Run-level rollback: an apply that fails mid-graph restores every
  touched destination to the previous generation — no half-applied
  deployments. Post-activation adapter failures never auto-rollback
  (a service that failed to start must not bounce your configs back)
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
- Activation adapters (SystemdUser, fonts via `fc-cache`, and
  desktop-entry via `update-desktop-database`)
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
- TypeScript frontend — bun-provisioned, version-locked, same IR; the
  repo's own install wins when it shadows the provisioned copy
- The griplint engine in-crate — all 22 linters as embedded data packs
  running in-process (the golden corpus replays byte-exact); no venv,
  no provisioning, no lifecycle for first-party linters
- Plugin lifecycle: `package = "owner/repo@tag"` provisions fetcher and
  linter binaries — sha256-verified, receipted, store-resolved
- Enterprise-grade GitHub releases: authenticated API downloads,
  host-scoped tokens, `version=` pins, bare-host `base_url`
- `[throttle]` token buckets + the `capabilities` op — rate budgets
  live in fetchers; `[throttle]` in env.toml outranks them, and
  buckets persist across runs
- **Constrained evaluation** ([plan 0013](https://github.com/gripsack-dev/gripsack/tree/main/plan/0013-constrained-evaluation.md)) —
  one frontend: TypeScript under a pinned, hash-verified Deno with
  deny-by-default capabilities (no env, no network, no subprocesses,
  read-only within the repo). Facts are injected by the core, not
  self-detected; host effects are declared probes the core binds in a
  two-stage eval, shown in `grip plan`'s host-inputs header. Host
  entrypoints are `defineEnv` functions — modules are pure values.
  The first eval of an unfamiliar repo is an explicit trust decision
  (`grip trust`, `GRIPSACK_TRUST_ALL` for CI). The Python frontend,
  bun, and uv are retired; the parity corpus became a golden IR
  snapshot corpus.
- **Content-addressed store identity** ([plan 0014](https://github.com/gripsack-dev/gripsack/tree/main/plan/0014-content-addressed-fetches.md)) —
  the hybrid: fetch-only and config-only modules name their store path
  by content hash (self-verifying; a mirror swap with identical bytes
  re-proves once and dedups to the same path), builds stay
  input-addressed so `grip plan` keeps plan-time naming. `store verify`
  is host-independent — the manifest carries the expectation.
- **`grip adopt`** ([plan 0015](https://github.com/gripsack-dev/gripsack/tree/main/plan/0015-grip-adopt.md)) —
  the adoption flow as a first-class command: point it at
  `~/.config/helix`, it explains what it sees, recommends `owned` vs
  `tracked_copy` with the reason, generates the module, shows the
  plan, and touches nothing until you confirm. The apply absorbs
  exactly the adopted destinations (scoped take-over) and records
  prior state — rollback, or undeclaring the module, restores your
  original files, bytes and permission bits. A fresh machine gets an
  empty generation 0, so adoption is always reversible.

## Next

Order is priority: adoption UX first, reliability of the core loop
next, ecosystems last.

- **Crash recovery for mutable destinations** — the generation flip is
  atomic, but the tracked_copy/merge/template writes before it are
  not: kill -9 or power loss mid-apply leaves touched destinations
  with no generation record. A durable apply journal (begin → backups
  → intents → fsync → commit) with startup reconciliation would make
  the mutable half crash-recoverable, not just failure-compensated.
- **Resolver executables** (0013 D8) — custom registries become
  `gripresolve-*` plugins on the same NDJSON envelope as fetchers:
  spawned with a scrubbed, declared-env-only environment (credentials
  never touch eval), network intent declared and shown in plan.
  **`grip update --dry-run`** folds in here — "resolve, don't write"
  is the natural read mode of an explicit resolve phase.
- **Rollback adapters** — user-initiated `grip rollback` re-runs
  post-link/post-activate adapters (the unified engine covers
  destinations; adapters still don't re-run on rollback).
- ~~Content-addressed store paths, deeper~~ — shipped as the 0014
  hybrid (above). A content-addressed fetch cache fell out as
  designed: presence of the content path IS the cache hit.
- **Module env inheritance for dependents** — a dependent sees the env
  its dependencies export (build-time today).
- **Secrets model** — references to external secret managers
  (age/sops/1Password), decrypted at activation; values never in the
  store, manifests, plans, or logs (0001 §7's seed, made public).
- **More probe kinds** — `executable` and `file_exists` shipped;
  `probe.command("wg", ["show"])` (a declared, core-run subprocess at
  bind time) is the next rung.
- **More reference fetchers** — `pip` (corporate PyPI mirrors) and the
  internal-registry patterns, out-of-tree like `gripfetch-apt`.

## North star

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.

