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
- Fetchers: `github_release` (with resolution + `{version}`
  substitution), `git`, `brew` (bottles, with the pour), `pixi`,
  bare binaries / `.tar.xz` / `.zip`
- `gripfetch-*` plugin fetchers — NDJSON over stdio, every byte
  hash-verified by the core
- Plugin protocol hardening: the locked pin travels in every request,
  provenance lands in the run log, stderr drains concurrently, and a
  600s deadline means no hangs
- `grip update [MODULE]` — the flake cycle, per-module
- `--repo` bootstrap (path or git URL), self-provisioning runtimes —
  bundled pixi and a pinned, sha256-verified Deno for eval, per platform
- `tree(...)` — directory-shaped config deploys
- Read-only store payloads — `chmod a-w` at publish: an app that
  rewrites an `owned` config through its symlink gets EACCES instead
  of silently corrupting the store
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
- 23 config linters — `griplint-*` for the tools your dotfiles
  actually configure (helix, yazi, starship, zed, claude-code, …),
  as data packs in `crates/griplint`, with a weekly upstream-watch
  that files freshness issues; see [linters](linters.md)
- Corporate proxy support, trusting the system CA roots, `NO_PROXY`
  honored
- Per-platform release matrix (linux + macOS, x86_64 + aarch64 — no
  Windows; WSL is the story), a homebrew cask, and a multi-platform
  install.sh, with a brew `version=` tripwire
- Run logs with causal spans; the debug and adopt skills
- `merge` + `template` ownership modes — a managed block inside
  foreign files (`.bashrc`), and payloads rendered from `{{ vars }}`
  at deploy time
- `grip init` — scaffold an env repo from the embedded template,
  package.json + tsconfig included (the IDE story)
- The griplint engine in-crate — all 23 linters as embedded data packs
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
  `~/.config/helix`, it explains what it sees, *asks* the ownership
  question with the semantics laid out (never guesses — the safe
  default is `tracked_copy`), generates the module, shows the plan,
  and touches nothing until you confirm. The apply absorbs exactly
  the adopted destinations (scoped take-over) and records prior
  state — rollback, or undeclaring the module, restores your original
  files, bytes and permission bits. A fresh machine gets an empty
  generation 0, so adoption is always reversible.
- **Structured `run` steps** (0007's middle rung): argv/env/cwd as
  data, no shell interpretation, declared outputs checked — and the
  `{arch.x64}` placeholder for node-style asset names
- **Pin integrity hardening** — a fetched apply can no longer drop
  pin metadata from the lockfile; the repo overlay hash (`repo256`)
  moves the pin when a config tree gains a file; store publishes
  survive a tmpfs `/tmp` (EXDEV copy fallback); deploys refuse
  destinations resolving into the env repo; git payloads hash the
  checkout, never the clone; and rollback restores the expanded
  install keys a generation actually deployed
- **Crash recovery for mutable destinations**
  ([plan 0019](https://github.com/gripsack-dev/gripsack/tree/main/plan/0019-deploy-journal.md)) —
  the deploy journal: every destination mutation (owned links,
  tracked copies, templates, merge blocks) records its prior state —
  file bytes into the content-addressed prior store, fsync'd —
  before the write; the generation flip is the run's commit point;
  and the next `apply` restores uncommitted entries under the
  lifecycle lock before deploying anything. A kill -9 mid-apply no
  longer leaves the filesystem between generations — and the drift
  guard applies on recovery: a file edited after the crash keeps the
  user's bytes. The transaction semantics were hardened by an
  external review
  ([plan 0020](https://github.com/gripsack-dev/gripsack/tree/main/plan/0020-review-response.md)):
  runs declare their target generation before mutating (a crash
  after the flip reads as committed, never restores a live
  generation's priors), corrupt recovery metadata fails closed into
  quarantine, only `NotFound` means "absent", cross-filesystem store
  publication is atomic, journal cleanup is durable, and `grip plan`
  labels every mutation's reversibility.
- **macOS behavioral CI + signed attestations** (plan/0020's two
  queued items, 0.20.0): the full flow suite runs natively on a
  macOS runner every push — its first runs found and fixed a real
  product bug (hostnames with dots broke `init` → `check`: the file
  name was sanitized, the lookup was not) plus two platform
  assumptions in tests; every release tarball now carries GitHub
  build provenance (`gh attestation verify`). The e2e harness was
  rebuilt for cross-platform CI: timing tests are self-relative (no
  wall-clock flakes), and failures print the grip run log — the
  macOS findings were debugged entirely from that output.

## Next

Order is priority: reliability of the core loop first, ecosystems
last. The first block is the review-round backlog — items three
external audits proposed and the project accepted but deliberately
deferred, each with its plan reference and trigger. (0025's breadth
freeze stands: nothing new in the ecosystem block until the
transaction items land.)

- **A machine-checkable transaction model** ([plan 0020](https://github.com/gripsack-dev/gripsack/tree/main/plan/0020-review-response.md), [0026](https://github.com/gripsack-dev/gripsack/tree/main/plan/0026-path-centric-transactions.md)) —
  a TLA+/Stateright (or property-tested Rust) model of the
  transaction state machine, now that it covers apply, prune, and
  rollback. Deferred twice with a recorded trigger: the protocol
  goes quiet for a full release cycle first — it grew in 0.22 and
  again in 0.23, so the clock starts now.
- **The full kill-point matrix** ([plan 0025](https://github.com/gripsack-dev/gripsack/tree/main/plan/0025-transaction-coverage.md)) —
  `GRIPSACK_CRASH_AFTER`-style aborts at every durable boundary
  (journal write, file and dir fsyncs, rename, flip, cleanup), each
  with the same oracle: previous generation, or committed target, or
  explicitly preserved user drift. Today the deploy, prune, and
  rollback windows are covered; the matrix is the remainder.
- **Signed update-channel manifest + install-time verification** —
  install.sh and `grip self-update` already verify the sha256
  sidecar; the next step is provenance verified *automatically* at
  install time (attestation-aware installer, signed channel
  manifest) rather than taught as a manual step ([plan 0020](https://github.com/gripsack-dev/gripsack/tree/main/plan/0020-review-response.md)
  queue; the 0025 review's install-order point folds in here).
- **Mode-aware identity** ([plan 0026](https://github.com/gripsack-dev/gripsack/tree/main/plan/0026-path-centric-transactions.md)
  §7 remainder) — Unix mode bits in the manifest/journal identity:
  chmod-only drift detection and exact mode restoration on rollback.
  Today the canonical hash covers the exec bit and content updates
  preserve the destination's mode; the full schema change is its own
  round.
- **Non-UTF-8 symlink targets end-to-end** ([plan 0021](https://github.com/gripsack-dev/gripsack/tree/main/plan/0021-cap-std-fs-hardening.md)
  pitfalls) — `OsStr` bytes through the journal and prior store;
  today's loud refusal becomes byte-preserving capture and restore.
- **`--force` for drift overwrite** ([plan 0026](https://github.com/gripsack-dev/gripsack/tree/main/plan/0026-path-centric-transactions.md)) —
  an explicit override for the preserve-and-warn default in apply
  and rollback. A product decision, not a safety gap — queued for an
  owner decision.
- **One-commit release modules** ([plan 0024](https://github.com/gripsack-dev/gripsack/tree/main/plan/0024-review-response-0.21.0.md),
  carried) — `update` writes `sha256` and the first `apply` adds
  `tree256` today, costing a second commit per module; fold
  finalization into `update`. The pixi hash split is the same item.
- **Persistent fuzz + fault harnesses in-repo** ([plan 0027](https://github.com/gripsack-dev/gripsack/tree/main/plan/0027-provable-transactions.md),
  fourth audit P2) — the playbook's harnesses live outside the repo
  today; land them under it (manifest parsing, merge-block parsing,
  archive extraction, journal recovery, GC reachability) with
  deterministic smoke budgets in CI and longer runs on a schedule.
- **A dedicated safety page** on the site (fourth audit) — one page
  separating atomic selection, journaled transitions, drift
  preservation, what metadata is restored exactly, the GC safety
  model, plugin execution trust, and backup recommendations. The
  guarantee table in architecture.md is the seed.

- **CycloneDX sidecar on releases** ([plan 0022](https://github.com/gripsack-dev/gripsack/tree/main/plan/0022-sbom-cargo-auditable.md)
  optional follow-up) — the in-binary SBOM is the primary form; a
  CycloneDX file attached to the GitHub release serves file-based
  scanners. Lands when a user asks.

- **Resolver executables** (0013 D8) — custom registries become
  `gripresolve-*` plugins on the same NDJSON envelope as fetchers:
  spawned with a scrubbed, declared-env-only environment (credentials
  never touch eval), network intent declared and shown in plan.
  **`grip update --dry-run`** folds in here — "resolve, don't write"
  is the natural read mode of an explicit resolve phase.
- **Rollback adapters** — user-initiated `grip rollback` re-runs
  post-link/post-activate adapters (the unified engine covers
  destinations; adapters still don't re-run on rollback).
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

