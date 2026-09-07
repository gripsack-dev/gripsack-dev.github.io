# Roadmap

Where gripsack is going. The north star: *a misconfiguration in any
file gripsack touches should produce the same quality of error as a
typo in a module.*

## Shipped

- **Contract fidelity and persistence** ([plan 0041](https://github.com/gripsack-dev/gripsack/blob/main/plan/0041-p1-contract-fidelity.md),
  core/TS 0.36.0) — fail-closed GC admission; explicit/declarative parity;
  real ordering-only `needs`; output gates; accurate warm preview; IR v3
  removes inert retries. Private-mode receipts and exact template rollback
  are corrected. Every recorded cut in six persistence scenarios is
  exercised with errors, process loss and user drift; a separate ordering
  model rejects the former EXDEV chmod-after-fsync bug. Physical power
  loss is not simulated.
- **Journey harness** (0.34.0, plan 0038) and **rollback activation**
  (0.33.0, plan 0037) — seeded stateful journeys are in CI; rollback
  replays the target generation's durable activation intents.

- **Build closures** ([plan 0039](https://github.com/gripsack-dev/gripsack/blob/main/plan/0039-build-closures.md),
  core/TS 0.35.0) — `dep(name, { for: "build" })` supplies store tools
  to build steps without deploying them. Transitive build-edge PATH,
  `GRIP_DEP_*`, payload receipts, and generation-pinned GC; pin changes
  rebuild consumers, rollback never does. IR v2 is a clean alpha
  cutover. See [dependencies and migration](modules.md#dependencies).

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
- **The machine-checked transaction model**
  ([plan 0028](https://github.com/gripsack-dev/gripsack/tree/main/plan/0028-machine-checked-model.md)) —
  and the guarantees now have their own page: [safety](safety.md) —
  atomic selection, journaled transitions, drift preservation, exact
  restoration, the GC model, plugin trust, and honest backup advice,
  each enforced by test or the model gate.

  the journal/flip/recovery protocol as an exhaustive state-machine
  model, driving the SHIPPED decision functions (classify/decide):
  every crash point, both crash kinds, every power-loss durability
  subset, with and without post-crash user edits — zero violations.
  Plus the protocol specced in TLA+ and TLC-checked in CI
  (`docker compose run model`), with the 0.22 roll-forward rule kept
  as a proven counterexample in both layers. The trigger fired early
  by owner override — the model is mutation-calibrated (a one-line
  classify mutant yields 136 violations).
- **Canonical destinations + hardened transaction identity**
  ([plan 0030](https://github.com/gripsack-dev/gripsack/tree/main/plan/0030-canonical-destinations.md),
  0.26.0) — one physical file has one identity everywhere:
  `~`/`$HOME`/absolute/symlinked-ancestor spellings of one directory
  entry are a check-time error (E119, span-labeled); a mid-apply
  external write aborts instead of clobbering; a second
  `--take-over` keeps the epoch's first origin; pre-0.23 journal
  markers refuse with guidance.
- **Mode-aware identity**
  ([plan 0031](https://github.com/gripsack-dev/gripsack/tree/main/plan/0031-mode-aware-identity.md),
  0.27.0) — the full permission mode joins the manifest/journal
  identity: chmod-only drift is detected and preserved like any
  drift, rollback restores the recorded mode exactly, and fresh
  writes land deterministic (umask-independent) modes. The lineage
  explorer models destination aliases and chmod drift, driving the
  shipped decision functions.
- **Durable activation hooks**
  ([plan 0032](https://github.com/gripsack-dev/gripsack/tree/main/plan/0032-durable-activation.md),
  0.28.0) — the last unrecorded crash window closes: the pending
  intent record is written BEFORE the flip, so a kill can't skip your
  service restarts or cache refreshes; the next run resumes them.
  Model-first: `specs/Activation.tla` is TLC-checked in CI; the
  pre-0.28 shape is a kept mutant that violates the NoSilentSkip
  invariant. Intents may run twice across a crash — idempotent by
  contract, documented.
- **The 0.27.0 review round**
  ([plan 0033](https://github.com/gripsack-dev/gripsack/tree/main/plan/0033-review-response-0.27.0.md),
  0.29.0) — take-over preserves a private file's mode (prior blobs
  land 0600 under a 0700 store dir); the deliberate-pin read grant
  validates the resolved package; step `needs` orders execution;
  plan runs the same gates as check/apply and marks opaque run steps;
  preserved drift blocks a mode switch. The lineage explorer drives
  the shipped `plan_link` across mode changes.
- **One shared operation list**
  ([plan 0034](https://github.com/gripsack-dev/gripsack/tree/main/plan/0034-shared-operation-list.md),
  0.30.0) — `ts → IR → ops → execute`: one planner computes the
  destination operations; `grip plan` renders them, apply executes
  them under the journal, rollback plans with the target generation's
  manifest as the desired state. Plan/apply agreement is by
  construction, with a VM-level harness proving the lifting (560
  materialized cases, 0.31.0).

## Next

Order is priority: reliability of the core loop first, ecosystems
last. The first block is the review-round backlog — items three
external audits proposed and the project accepted but deliberately
deferred, each with its plan reference and trigger. (0025's breadth
freeze stands: nothing new in the ecosystem block until the
transaction items land. Model-first since 0032: new
transaction-adjacent protocols get an exhaustive model before or
with the implementation — the Rust harness driving shipped decision
functions for string/path mechanics, TLA+ (TLC in CI) for protocols.)

- **P2 — Bounded acquisition and subprocess supervision**
  ([0040 H](https://github.com/gripsack-dev/gripsack/blob/main/plan/0040-project-sweep.md)) —
  streaming extraction and aggregate acquisition limits; bound stdout
  queues, stderr lines and retained diagnostics; make deadlines cover
  reaping and inherited pipes. Shared process mechanics only after the
  two hosts' distinct contracts are pinned. Ahead of ecosystem breadth.
- **P2 — Causal worker tracing and reliable log selection** (0040 I) —
  carry run/module spans across worker threads and select the explicit
  latest pointer, not filename ordering. Require real emitted ancestry
  and concurrent-run coverage.
- **P2 — Executable documentation and contract coverage** (0040 J) —
  execute published examples and cover consumer-visible field behavior
  across schema/DSL/core; the P1 parity and retry fixes are shipped, not
  substitutes for continuing drift prevention.
- **P2 — Reproducible toolchains and update publication** (0040 L) —
  deliberate Rust/Deno/image pin updates and durable unique self-update
  staging. Keep install-time provenance below as its separate trust decision.
- **Signed update-channel manifest + install-time verification** —
  install.sh and `grip self-update` already verify the sha256
  sidecar; the next step is provenance verified *automatically* at
  install time (attestation-aware installer, signed channel
  manifest) rather than taught as a manual step ([plan 0020](https://github.com/gripsack-dev/gripsack/tree/main/plan/0020-review-response.md)
  queue; the 0025 review's install-order point folds in here).
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
- **P2 — Persistent fuzz harnesses in-repo** ([plan 0027](https://github.com/gripsack-dev/gripsack/tree/main/plan/0027-provable-transactions.md)) —
  manifest/merge/archive parsing, recovery and GC corpora with bounded CI
  smoke runs and longer scheduled runs. The recorded-cut persistence
  matrix has landed in 0.36.0; parser fuzzing remains.
- **Explicit drift resolution: `grip resolve`** ([plan 0030](https://github.com/gripsack-dev/gripsack/tree/main/plan/0030-canonical-destinations.md);
  named the next product capability by two external reviews) —
  `--keep-live` / `--apply-repo` / `--adopt-live` per destination,
  and an explicit origin-rebase, instead of preserve-and-warn plus
  global `--take-over`.
- **P2 — Fetch and resolved-graph reuse** (0033/0035/0040) —
  HTTP-client reuse and memoized resolved graph identities; aggregate
  memory/process bounds are covered by the higher-priority item above.
- **Compare-and-swap displacement** (0030) — `renameat2`/
  `renameatx_np` give the mutation step atomic compare-and-swap where
  the platform allows it; the precondition-at-mutation holds
  meanwhile.
- **Cross-module merge aggregation** (0030 H6) — several modules'
  blocks in ONE file as a single whole-file transition; E111/E119
  reject sharing until then.
- **Reproducible-build verification + an external audit** (fifth
  audit, supply-chain list) — prove one release target rebuilds
  byte-identically, and put a stable release candidate in front of an
  independent reviewer. Prerequisite per the same audit: a quiet soak
  cycle first — no transaction-schema churn next release.
- **`allow_outside_home` setting** (fifth audit, finding 12
  half-adopted) — outside-home absolute destinations are allowed today
  (same-privilege by design; real usage exists). An explicit setting
  with louder plans is the hardened shape. The safety page documents
  the actual boundary now.

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
- **Module env inheritance for dependents** (0039: stays separate) —
  decide precedence and variable expansion for general dependency
  exports. Build closures supply PATH and `GRIP_DEP_*` only; they do
  not inherit activation-profile `env`. Existing priority retained.
- **Secrets model** — references to external secret managers
  (age/sops/1Password), decrypted at activation; values never in the
  store, manifests, plans, or logs (0001 §7's seed, made public).
- **More probe kinds** — `executable` and `file_exists` shipped;
  `probe.command("wg", ["show"])` (a declared, core-run subprocess at
  bind time) is the next rung.
- **More reference fetchers** — `pip` (corporate PyPI mirrors) and the
  internal-registry patterns, out-of-tree like `gripfetch-apt`.
- **Library/header build exports — low priority, demand-driven**
  (0039 brainstorm) — consider `provides`/library/include paths only
  when a real consumer fixture needs them. Below the reliability
  backlog; no speculative environment variables shipped.
- **Controlled build PATH — low priority, opt-in design first**
  (0039 brainstorm) — investigate one global strict-build setting,
  including an explicit system-tool baseline and fixture impact.
  Do not silently turn today's prepend-only PATH into a hermetic
  environment. Existing builds use ambient shell/coreutils.

## North star

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.

