# How gripsack stays safe

Gripsack changes files you care about. This page says exactly what protects them: what is proved, what is tested, what is assumed and what is not claimed. If a sentence here is not true of the released code, it is a bug.

## The idea: rings

The rings separate decisions from effects. The kernel sees typed observations, not files: it can decide whether the observed object may be replaced. It cannot establish that the host read the right object, that a sync reached disk, or that another process stayed out of the way.

{anim:rings}

| Ring | What lives there | How it is checked |
|---|---|---|
| **Kernel** | Decide which generation committed, what may be written or deleted, and whether an update may publish a lock | Lean 4 proofs over a translation of the shipped Rust |
| **Protocol** | Kernel machines issue commands for apply, rollback, recovery, GC, journaling and activation | Machine decisions and ordering are proved; composition with storage is crash-injection tested, not proved |
| **Host** | Drivers observe destinations, issue filesystem calls, supervise processes and read store records | Persistence and fault-injection tests under explicit filesystem assumptions |
| **Edge** | TypeScript evaluation, downloads, archives, Conda, Docker, systemd | Sandbox, typed admission, hash-verified bytes, fuzzing |
| **Product** | The CLI, review, adopt, doctor | End-to-end flows against the real binary |

## What is proved in core {core_version}

The `proofs` release gate uses [Charon and Aeneas](https://github.com/AeneasVerif/aeneas) to translate the dependency-free Rust crate `gripsack-kernel` to Lean 4. It rejects drift from the checked-in translation, builds the proofs, and [audits the kernel theorems](https://github.com/gripsack-dev/gripsack/blob/{release_source}/proofs/Audit.lean) for axioms beyond `propext`, `Classical.choice` and `Quot.sound`. Deliberately broken variants of the Rust must fail their designated proofs. The gate covers the kernel's decisions, not the compiled binary or its host drivers.

**Commit classification.** After an interruption, recovery compares three selection identities: `current`, the recorded `previous` and the recorded `target` of the interrupted transaction.

- *Committed* if and only if `current` equals `target`.
- *Uncommitted* if and only if the run was fresh with no `current`, or `current` equals `previous` and not `target`.
- *Ambiguous* otherwise, which stops every further mutation until you look.

A higher generation number never grants commit authority; only identity does. Each transaction carries a 32-byte identifier compared byte for byte.

**Garbage collection.** GC refuses if recovery or activation is pending, or if `current` names a generation absent from the inventory. Pruning considers the oldest generations beyond `keep_generations`, never the current one. The kernel keeps predecessors required by retained manifests and authorizes deleting a store object only if no retained manifest or external root in the host's inventory names it.

**Journal publication.** The machine orders the publication of a record: stage, sync the file, publish the name, sync the directory. It commands a destination write only after the host acknowledges durable intent, accepts the write only if the host observes the intended object, and removes the run marker only after the record barrier.

**Crash recovery.** Recovery is a machine in the kernel that observes one destination at a time and issues one command at a time. It mutates only after the interrupted transaction is classified, never restores a destination it cannot restore exactly (it refuses by name instead), and removes the journal's run marker only after the record barrier.

**Apply, ownership and drift.** The apply machine authorizes a whole-file write only over absence, what gripsack last wrote there, or an object you explicitly consented to take over. A destination is released only when no unit of the run still claims it. This matters on case-insensitive filesystems: a change in spelling alone must not delete the object under its new name. The machine authorizes the switch only after every unit supplied by the host and every directory step has settled; a refused step stops the run before the switch.

**Managed blocks.** Replacing a block preserves the bytes outside its markers. Inserting a new block preserves the existing text and adds a separating newline if needed. Applying the same block twice changes nothing; removal requires the block to be intact and keeps the surrounding bytes.

**Activation.** Before each hook, the machine requires a durable start record and an observation that its generation is still current. If a hook switches generations, the next hook in the superseded batch is not launched. This governs dispatch, not what a hook does. The kernel allocates generation numbers above the durable high-water mark and does not authorize publishing the same generation twice.

**Updates.** `grip update` writes a lock only when every selected package was checked, none failed and something changed; each package is counted exactly once.

**Rollback.** A whole-file restore must install the target generation's recorded identity (bytes and mode, or link target), from retained content, only over absence or gripsack's own write. The machine never commands a restore inside a published generation. It counts the unit as restored only when the host observes that identity, and switches under a fresh transaction only after every supplied unit is settled. If the host cannot reproduce the target identity for a required write, rollback refuses before the switch.

The [verified-foundation design record](https://github.com/gripsack-dev/gripsack/blob/{release_source}/plan/0056-verified-foundation.md) includes both implementation records and future goals. For what shipped, see the [proof sources](https://github.com/gripsack-dev/gripsack/tree/{release_source}/proofs) and [kernel](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates/gripsack-kernel). The [0.56 release](changelog.md) changed typed path resolution and task output, not kernel transitions or proof premises.

## What is tested, not proved

These guarantees depend on more than a decision over typed inputs:

- **Crash safety end to end.** Tests run kernel machines with a crash-injecting in-memory filesystem. For example, they interrupt a rollback, interrupt recovery again, then check that each destination has its prior or target identity after recovery. This tests the composition for the exercised runs; it is not a theorem about all crash histories or the real filesystem.
- **Directory changes.** Apply and rollback keep whole-file writes out of destinations held by the directory protocol and reject steps out of order. The directory implementation itself is host code: TLA+ models and end-to-end tests check its contract (premise D below).
- **Source approval.** Approval binds the exact captured source bundle and policy; evaluation runs in a Deno sandbox with no environment, network or subprocess access.
- **Content integrity.** Downloads are hashed and verified before extraction; the store is sealed read-only and published by rename.

## What is assumed

The pure machines act on the observations and acknowledgments they receive. Interpreting those as facts about a Linux machine relies on the following storage assumptions (S1–S7 in the design record):

- **S1** `rename` within a directory is atomic and replaces the target; `RENAME_NOREPLACE` and exclusive `mkdir` fail if the name exists; `remove_dir_all` is a sequence of unlinks, not atomic.
- **S2** File data is durable after `fsync(file)`; a name is durable after `fsync(parent)`.
- **S3** Two crash kinds: a *kill* loses nothing already in the page cache, a *power loss* may lose any subset of non-durable operations consistent with completed barriers.
- **S4** One lifecycle writer at a time, held by an advisory lock released when the holder dies.
- **S5** External writers exist and are only *detected*, see below.
- **S6** The host must identify equivalent destination names consistently. It detects case-only aliases that resolve to one object (as on WSL's `/mnt/c`); names a filesystem equates only after Unicode normalization are not detected.
- **S7** Equal SHA-256 digests mean equal bytes.

**Directory premise D.** A directory step changes only the namespace named by its receipt and journals before its first change. A “settled” result means the recorded shape is in place; an interrupted or refused change must be recoverable through its journal. The [directory fence](https://github.com/gripsack-dev/gripsack/blob/{release_source}/crates/gripsack-kernel/src/directory.rs) relies on this host contract; the Lean proof does not establish it.

The proof chain also trusts the Charon/Aeneas translation and Lean's kernel. Running the resulting program adds the Rust compiler, the Linux kernel and the host hardware to that trust boundary.

## What is not claimed

- **The external-writer window.** Without explicit take-over, the ownership check protects a changed object it observes. Another process can still change that object between the driver's final re-check and its rename or unlink. That edit can be lost.
- **Effects outside managed files.** Hooks, tasks, services and anything a package's own program does are not transactions. Rollback restores files and launchers; it does not undo a database migration or a command you scheduled.
- **Liveness.** The proofs say what a recovery *may* leave behind, not that it always completes.
- **The world.** Docker Engine, systemd, Deno, Conda channels, registries, the OS and the hardware are outside every proof.
- **Platform.** Linux x86_64 and WSL2 only.

## Why proofs instead of more tests

Gripsack's guarantees used to be documented one review at a time, each with its own model and its own evidence receipt. That did not scale and it was hard to read. Since 0.52 the rule is simple: a guarantee is a theorem over the shipped code, a test that guards behavior you can see, or a bug-finder that has caught a real bug. Anything else goes. A release is the exact source passing its gates, and the proof gate runs alongside the test suites, not as a separate evidence process.
