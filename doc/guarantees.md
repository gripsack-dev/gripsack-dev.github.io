# How gripsack stays safe

Gripsack changes files you care about. This page says exactly what protects them: what is proved, what is tested, what is assumed and what is not claimed. If a sentence here is not true of the released code, it is a bug.

## The idea: rings

The rings separate decisions from effects. The kernel sees typed observations, not files: it can decide whether the observed object may be replaced. It cannot establish that the host read the right object, that a sync reached disk, or that another process stayed out of the way.

{anim:rings}

| Ring | What lives there | How it is checked |
|---|---|---|
| **Kernel** | Decide which generation committed, what may be written or deleted, and whether an update may publish a lock | Lean 4 proofs over a translation of the shipped Rust |
| **Protocol** | Kernel machines issue commands for apply, rollback, recovery, GC, journaling and activation | Journaled leaf writes and recovery cleanup have storage-level proofs. Tests also inject crashes into complete recovery runs. |
| **Host** | Drivers observe destinations, issue filesystem calls, supervise processes and read store records | Persistence and fault-injection tests under explicit filesystem assumptions |
| **Edge** | TypeScript evaluation, downloads, archives, Conda, Docker, systemd | Sandbox, typed admission, hash-verified bytes, fuzzing |
| **Product** | The CLI, review, adopt, doctor | End-to-end flows against the real binary |

## What is proved in core {core_version}

The `proofs` release gate uses [Charon and Aeneas](https://github.com/AeneasVerif/aeneas) to translate the dependency-free Rust crate `gripsack-kernel` to Lean 4. It rejects drift from the checked-in translation, builds the proofs, and [audits their transitive axioms](https://github.com/gripsack-dev/gripsack/blob/{release_source}/proofs/Audit.lean) against `propext`, `Classical.choice` and `Quot.sound`. Deliberately broken variants must fail their designated theorems. The filesystem model is checked in Lean; the compiled binary, host driver and physical disk are not.

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

The [verified-foundation RFC](https://github.com/gripsack-dev/gripsack/blob/{release_source}/docs/rfcs/2026-11-08-verified-foundation.md) includes both implementation records and future goals. For what shipped, see the [proof sources](https://github.com/gripsack-dev/gripsack/tree/{release_source}/proofs) and [kernel](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates/gripsack-kernel). In [0.57](changelog.md), debug and release builds use the same recovery machine. Removing the old debug route does not add a theorem about filesystem behavior.

### What has to survive a crash?

Suppose a leaf file is about to be replaced. Recovery needs the marker for **this transaction**, the entry for **this destination**, and the original content named by that entry. A file sync alone can leave complete bytes with no durable name. A directory sync alone can leave the right name pointing to incomplete bytes.

Core 0.58 [proves that the evidence is readable](https://github.com/gripsack-dev/gripsack/blob/{release_source}/proofs/Protocol/Leaf.lean) **before the write**: after process death and in every power-loss image allowed by the model. If a run writes the same file twice, both the original prior and the immediate before-image remain recoverable at that cut. Killing the process is not a disk test: the next process can still see unsynced writes in the page cache.

**Seeing a later user edit is not permission to discard undo evidence.** An unsynced replacement can vanish on power loss and expose an intermediate version. Recovery now rechecks and syncs the observed regular file and its parent, or seals the name of a rechecked symlink, before accepting it as preserved. A failed sync stops cleanup. The [settlement proof](https://github.com/gripsack-dev/gripsack/blob/{release_source}/proofs/Protocol/Preservation.lean) is about those barriers; it does not assume the external writer already made its edit durable.

**When may recovery remove the undo record?** Core 0.59 [proves the leaf cleanup rule](https://github.com/gripsack-dev/gripsack/blob/{release_source}/proofs/Protocol/RecoveryCleanup.lean). For an uncommitted run, each leaf has already reached its prior or the exact user edit recovery preserved. For a committed run, the selected generation remains identifiable: if any old undo record survives, the matching marker still tells the next reader not to apply it. Syncing the journal *between* removing the records and removing the marker is essential. The final sync makes the marker's removal durable too.

A failed sync stops further cleanup even if some writes reached disk. A restarted reader may find fewer records, or see a legitimate older journal with no marker. The proof covers the leaf cases and the specified interrupted cleanup cuts, not every sequence of crashes, directory repairs, hooks or eventual completion.

The power-loss question applies to disk-backed filesystems that honor the file and directory sync assumptions. On tmpfs, killing a process leaves its files visible, but reboot discards them. In WSL2, distinguish the guest filesystem from a mounted Windows volume: the latter does not automatically provide the same persistence or name matching.

## What is tested, not proved

These guarantees depend on more than a decision over typed inputs:

- **Crash safety end to end.** Tests run kernel machines with a crash-injecting in-memory filesystem. For example, they interrupt a rollback, interrupt recovery again, then check that each destination has its prior or target identity after recovery. This tests the composition for the exercised runs; it is not a theorem about all crash histories or the real filesystem.
- **Directory changes.** Apply and rollback keep whole-file writes out of destinations held by the directory protocol and reject steps out of order. The directory implementation itself is host code: TLA+ models and end-to-end tests check its contract (premise D below).
- **Evaluation sandbox.** There is no approval step: local repositories are trusted and remote ones are trusted on first use. Evaluation runs in a Deno sandbox with no environment, network or subprocess access.
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
