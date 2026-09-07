# Changelog

User-visible changes per release. Design archaeology lives in
`plan/`; this file is for "what's new for me".

## [0.38.0] — 2026-09-07

Migration feedback, permission identity, and honest read-only updates (0043).

### Added

- **`grip update --check`** resolves and acquires into private scratch, reports
  would-be pin changes, and leaves the lockfile and source cache unpublished.
  Exit 0 means current; exit 1 means changes are available. Recipes never run.
- **Permission-policy model coverage**: a corrected `FileMode.tla`, twelve
  positive lanes and four named counterexamples, plus a Rust explorer driving
  the shipped planner/executor through copy, template, merge, and link modes.

### Fixed

- **Executable templates stay executable.** Templates and tracked copies share
  fresh 0755/0644 source-executability policy and preserve acquired access on
  updates. SHA-256 identity includes rendered bytes and full permissions.
  Chmod-only drift is visible in plan, preserved with a warning on apply and
  rollback, and never authorizes prune—even after repeated observations.
  Templates add no in-file banner; their manifest is the identity record.
- **Merge markers record the hosting-file mode** alongside the block hash.
  New hosts use planner-selected 0644; existing hosts keep their permissions.
  Old markers upgrade in place. Chmod drift guards reapply and prune without
  changing unmanaged content; store verification reports destination drift
  without treating it as store corruption or deleting healthy artifacts.
- **Doctor checks the installed frontend**, not just the declared npm range.
  A stale local `node_modules/@gripsack/core` is a MISS even with a newer
  package.json declaration. Advice names both updating and removing the pin.
- **Tuicr pack coverage is 0.20–0.25**, with real `[forge]` and `[export]`
  sections and a migration hint for `export_legend`. Supported v0.22 configs
  no longer produce the stale-coverage warning; v0.19 still does.

IR remains v3; old lockfiles and generations remain readable. Legacy template
receipts authorize changes only when both the bytes hash and recorded mode
match. Core and `@gripsack/core` ship together at 0.38.0.

## [0.37.0] — 2026-09-07

Complete source pins, bounded acquisition, and stronger protocol evidence
(plan/0042).

### Added

- **One-commit source updates**: `grip update` acquires and verifies selected
  sources, captures repo overlays, and completes their pins before replacing
  the lockfile once. Source-only artifacts are cached without deployment;
  build recipes and activation hooks never run during update. Warm and cold
  apply preserve completed lock bytes. A failed update leaves the old lock intact.
- **Independent acquisition limits**: two concurrent payloads by default,
  512 MiB downloaded and 4 GiB expanded per payload, 100,000 entries and
  a 128 MiB decoder budget. Positive `[settings]` values override these limits.
  Verified private spools replace payload-sized memory buffers; archive path,
  link, metadata and actual decoded-byte limits fail before publication.
- **Bounded protocol supervision** for fetchers, capability probes and linters:
  request/line/output/diagnostic caps, retained stderr tails, nonblocking pipes,
  owned process groups and deadlines that include cleanup. Cleanup failures
  are reported; kernel progress remains an explicit assumption.
- **Executable published examples**, checked against the actual npm package
  and core, plus persistent manifest/merge/archive/recovery/GC fuzz corpora.
  Repeated-recovery, activation, process-supervision and concurrent-publication
  models carry positive checks and calibrated counterexamples.

### Fixed

- Pixi pins use the installed primary-package version and the core-harvested
  tree hash consistently in update and apply; conda bookkeeping is excluded.
  Locked bottle URLs and versions survive registry changes during reconstruction.
  Git branch/tag declarations are frozen to their resolved commit, so a moved
  upstream ref cannot break a pinned cold reconstruction.
- Repo overlays are hashed from a private snapshot, replace leaf symlinks rather
  than following them, and refuse fetched symlink ancestors. Missing overlays
  invalidate cached merged trees; directory and dangling source links retain
  consistent content identity.
- Self-update serializes per executable, rechecks the installed version under
  its lock, selects one regular executable, and publishes bytes and mode durably.
  Post-rename durability failures never roll the executable back.
- Worker and step logs retain their run ancestry. Failed-test diagnostics use
  the explicit latest-run pointer, with a validated timestamp fallback.
- IR v3 rejects silent-drop fields in nested tagged nodes and spans; JSON Schema
  structural admission follows the parser. Valid step-intent triggers are accepted.

### Changed

- Rust, Deno, base images and release tooling are deliberately pinned. A
  two-clean-build runner records exact image/lock/toolchain inputs and compares
  release binaries; it makes no universal cross-time reproducibility claim.
- The SDK exports a closed `Build` type shared by `module()` and `buildStep()`.
  IR stays at v3; existing lockfiles and generations remain readable. Update a
  deliberate SDK pin to `@gripsack/core@^0.37.0`.

## [0.36.0] — 2026-09-07

Contract fidelity and persistence evidence (plan/0041), followed by a
placement and representation review.

### Fixed

- **GC fails closed before deletion** on malformed module/build-closure
  store roots or invalid/unreadable retention configuration, including
  dangling config links. Missing repair artifacts remain valid references.
- **Explicit steps keep module contracts**: source staging, config lint
  and pre-flip module verification use the same prepared view as data-style
  modules. Failed verification cannot commit a generation.
- **Cross-module `needs` actually orders work**, including subset applies.
  These are scheduling-only edges, not runtime/build roles or PATH exports.
  Activation targets, self-qualified refs and mixed graph cycles fail early.
- **Shell outputs are enforced**, like structured-run outputs. Warm preview
  uses the same concrete source construction and artifact identity as apply.
- **Private-file takeover records the identity actually written**. Content
  updates retain acquired permissions; source execute-bit changes do not
  grant read/write access. Store verification checks source executability
  and the receipt's mode domain; older private-copy receipts stay valid
  instead of letting repair delete healthy retained payloads.
  Template rollback restores exact permissions, even with unchanged bytes.
- **EXDEV publication syncs final permissions before publishing**; directory
  creation and publication participate in the durability boundary.

### Changed

- **Breaking alpha cutover to IR v3**: inert module/step `retries` fields
  are removed, not silently ignored. Update pinned `@gripsack/core` to
  `^0.36.0`, or use the embedded frontend. v1/v2 schemas remain historical;
  lockfiles and generations remain readable.
- Build/custom-shell/run steps are explicitly **cached artifact recipes**.
  Outputs are postconditions, not an "always run" switch. Use activation
  hooks for repeatable effects. Cross-module needs are module-granular.

### Internal

- Debug-only persistence matrix: every recorded cut in apply/deploy,
  apply/prune, rollback/deploy, rollback/prune and forced-copy scenarios,
  with I/O errors, abrupt process loss and subsequent user drift. A separate
  Rust trace model checks ordering and rejects the old chmod-after-fsync
  sequence; this is not a physical power-loss simulator.
- Cohesive lifecycle, producer and verification modules; flow tests split
  by invariant; filesystem/journal unit suites separated from production.

## [0.35.0] — 2026-09-06

Build closures (plan/0039) — a build dependency is no longer a
deployed one.

### Added

- **`dep(name, { for: "build" })`** — build-only dependencies are
  fetched and stored, never deployed merely to serve a compile.
  Build/custom/run steps prepend the transitive closure's `bin/`
  directories to PATH and receive `GRIP_DEP_<NAME>` store roots.
  Any runtime incoming edge still requires normal deployment.
- **Payload receipts and retained-history GC** — build-only manifest
  records keep verification receipts but no destinations, activation
  intents, or profile exports. Consumers record `build_closure`; all
  retained generations pin those paths until GC prunes that history.
- **Fresh dependency pins reach consumers immediately** — a cold
  apply followed by a warm one reuses the artifact; direct or
  transitive pin changes rebuild it. Rollback never rebuilds.
- Unknown `for` values receive source-labeled **E122** diagnostics.
  Ambiguous normalized `GRIP_DEP_*` names are rejected with **E123**.

### Changed

- **Breaking alpha cutover to IR v2** — `Dependency.for` replaces
  `edge`; the core accepts v2 only and rejects v1 before field
  decoding. The v1 schema remains historical documentation.
  Lockfiles and persisted generations remain readable.
- **`dep()` takes an options object** —
  `dep("rust", "build")` becomes `dep("rust", { for: "build" })`.
  `dep("git")` still defaults to runtime. Update pinned
  `@gripsack/core` to `^0.35.0` or remove the pin to use the embedded
  frontend. Core and TypeScript 0.35.0 ship together.

## [0.34.0] — 2026-09-06

The journey harness (plan/0038) — stateful property tests of user
time, and the bug it caught on its first day.

### Fixed

- **`store verify` no longer reports false corruption on preserved
  entries** — a preserved-drift record describes an OBSERVATION, not
  a store deployment; verify skips it. Found by the harness, covered
  by it.

### Internal

- `e2e/test_journey.py`: seeded random declare/apply/drift/take-over/
  undeclare/respell/rollback/update journeys against the real binary,
  with a per-destination expectation model (0029 §2 drift and prune
  semantics included) and system oracles (check, store-verify,
  generation monotonicity) after every step. Five fixed seeds; a red
  run prints its op trace.

## [0.33.0] — 2026-09-06

Rollback activation (plan/0037) — the roadmap's rollback-adapters
item, prioritized after the 0.31.0 review.

### Changed

- **`grip rollback` restores the RUNNING environment** — the target
  generation's recorded intents (service restarts, cache refreshes,
  custom hooks) re-run after the flip, durable through the same
  pending record apply uses: a kill mid-rollback-adapters resumes
  them on the next run. Modules the rollback undeclares fire their
  `on_remove` hooks. Adapter failures warn, never un-rollback.

## [0.32.0] — 2026-09-06

The fb11aaf external-review round (plan/0035) — the first review
against the shared-op architecture. Ownership identity is canonical
everywhere, verification has receipts, and `cargo install` works.

### Fixed

- **A spelling-only declaration change no longer deletes the file** —
  the manifest records the canonical destination key next to the
  declared spelling; prune, rollback, lineage, and `why-owns` all key
  on it. The reviewer's headline defect.
- **A failed verifier fails every retry** — store presence is not a
  receipt: verification runs unless a COMMITTED generation verified
  the identical produced state with identical checks; the receipt
  rides the manifest.
- **A typo'd module field (`confg:`) fails eval with a
  did-you-mean** — the TypeScript constructor rejects unknown fields
  at runtime, so a typo can never lower to an empty desired state and
  prune your files.
- **A dependency's pin update rebuilds its consumers** — the build
  key incorporates the dependency's RESOLVED identity (transport
  hash, tree hash, version), not just its declaration.
- **The activation-record write is inside the transaction boundary**
  — a failure between the first mutation and the flip compensates;
  an unreadable record blocks new mutations.
- **`cargo install gripsack` and the mise cargo route work** — the
  frontend is vendored into the crate as generated Rust (no
  build-time read of the repo tree); packaging CI asserts it.
- **Preview is read-only and accurate** — plan creates no
  directories, a satisfied owned link reads satisfied, and a deferred
  fetched destination is never shown as a prune.
- **Explicit steps carry their payload sources** — overlay and
  identity walk the normalized step graph; cross-phase `needs` that
  can't be honored are E121 at check (post-deploy effects belong in
  activate hooks).
- **`on_remove` hooks fire at removal, not install** — triggers
  survive expansion, and a removed module's hooks run from the
  previous generation's record.
- **Repo build env can't redefine operator policy** — `[eval] env`
  rejects `GRIPSACK_*` (a reserved namespace) and applies after
  runtime selection.
- **Store publication fsyncs the staged tree recursively** before the
  rename — payload bytes are durable before the final name exists,
  on the same-filesystem path too.

### Internal

- `DeployedEntry` fields are typed: `from`/`key` are paths, `hash` is
  a `ManifestHash` (constructible only from the typed producers),
  `prior` is the enum. The reviewer's `DestinationKey` ask, landed.
- Module runs take a named `ModuleInputs` bundle — no more
  nine-positional-argument signatures.

## [0.31.0] — 2026-09-06

The VM-level model harness (plan/0034's explorer extension, landed).

### Internal

- `ops/model.rs`: enumerated abstract states (absent / file at three
  modes / foreign symlink × desired content × manifest lineage ×
  take-over) are materialized onto a real filesystem, planned with
  the shipped `plan_entry_op`, and executed with the shipped
  `execute_op` — 560 cases, checked: the planner's decision IS the
  algebra's answer (plan_copy/plan_link), and the executed op lands
  exactly its recorded intent. Plan/apply agreement now has a
  machine-checked floor, not just a by-construction argument.

## [0.30.0] — 2026-09-05

One shared operation list (plan/0034) — the architecture the 0.27.0
review called for: `ts → IR → ops → execute`. One planner computes the
destination operations; `grip plan` renders it, apply executes it,
rollback plans with the target generation's manifest as the desired
state. Plan/apply agreement is by construction.

### Changed

- **`grip plan` renders the operation list apply executes** — the
  separate preview engine is gone. Drifted destinations preview as
  "drifted — kept (apply preserves)" instead of the old "(update)"
  lie, and run/shell-step modules always show their opaque effects.
- **Rollback plans through the same planner** — the Transition
  machinery and the separate restore path are deleted; `plan_copy`'s
  three-way is the rollback drift rule.

### Internal

[Showing lines 1-300 of 1584. Use :301 to continue]