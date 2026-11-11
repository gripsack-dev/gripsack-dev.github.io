# How gripsack stays safe

Gripsack changes files you care about. This page says exactly what protects them: what is proved, what is tested, what is assumed and what is not claimed. If a sentence here is not true of the released code, it is a bug.

## The idea: rings

The code is arranged in rings. The center holds pure decisions over typed data with no IO at all. Each ring outward holds less trusted code and is checked in a cheaper way, and it trusts only the rings inside it. Code moves *inward* to gain a guarantee; nothing is modelled on the outside.

{anim:rings}

| Ring | What lives there | How it is checked |
|---|---|---|
| **Kernel** | Pure decisions: which generation is committed, what may be written or deleted, in what order a journal record becomes durable, when a lock may be published | **Proved in Lean 4** over a translation of the shipped Rust |
| **Protocol** | Apply, rollback, recover and GC as state machines that observe, decide and issue one command at a time | Apply, rollback, recover, GC, the journal run and activation: each decision proved in Lean; crash safety end to end crash-injection tested over an in-memory filesystem |
| **Host** | The driver loop, filesystem access, store layout, locks | Small enough to read; every assumption listed; fault injection and crash tests |
| **Edge** | TypeScript evaluation, downloads, archives, Conda, Docker, systemd | Sandbox, typed admission, hash-verified bytes, fuzzing |
| **Product** | The CLI, review, adopt, doctor | End-to-end flows against the real binary |

## What is proved today (0.54)

The kernel is a dependency-free Rust crate, `gripsack-kernel`. The `proofs` release gate translates it to Lean 4 with [Charon and Aeneas](https://github.com/AeneasVerif/aeneas) and proves 579 theorems over that translation. There is no hand-written Lean copy of the Rust: the proofs are about the bytes that ship. The gate also checks that every theorem uses only Lean's three standard axioms (`propext`, `Classical.choice`, `Quot.sound`) and that each of 113 deliberately broken variants of the Rust fails exactly the theorem that should catch it.

**Commit classification.** After an interruption, the next command looks at three generation identities: `current`, the recorded `previous` and the recorded `target` of the interrupted transaction.

- *Committed* if and only if `current` equals `target`.
- *Uncommitted* if and only if the run was fresh with no `current`, or `current` equals `previous` and not `target`.
- *Ambiguous* otherwise, which stops every further mutation until you look.

A higher generation number never grants commit authority; only identity does. Each transaction carries a 32-byte identifier compared byte for byte.

**Garbage collection.** `grip gc` may proceed only when no recovery is pending and `current` names a generation in the inventory. Pruning selects exactly the oldest generations beyond your `keep_generations`, in order, never the current one and never anything newer than the cut. Every deletion GC makes is decided by the kernel: a store path is removed only if no retained generation references it, the retained set is closed under references, and the current generation is never retired.

**Journal publication.** A journal record becomes durable through exactly one order: stage, sync the file, publish the name, sync the directory. Every destination write in a run happens only after its intent is durable, a write is accepted only when what landed is what was intended, and the run marker is removed only after the record barrier.

**Crash recovery.** Recovery is a machine in the kernel that observes one destination at a time and issues one command at a time. It mutates only after the interrupted transaction is classified, never restores a destination it cannot restore exactly (it refuses by name instead), and removes the journal's run marker only after the record barrier.

**Apply, ownership and drift.** `grip apply` is a machine in the kernel. Over every run, a write lands only on absence, on exactly what gripsack last wrote there, or on an object you explicitly consented to take over with `--take-over`, and it installs exactly what the unit declares. A file you changed is never written; a file gripsack never recorded is refused. A destination is released only when no unit of the run still claims it, so changing only the case of a name on a case-insensitive filesystem no longer deletes the file. The switch to the new generation comes only after every unit and every directory step is settled, and a refusal stops the run before it.

**Managed blocks.** A managed block changes only the bytes between its markers: everything outside is preserved exactly, applying the same block twice changes nothing, and removing a block you did not edit restores the file as it was.

**Activation.** Hooks run in ledger order, and each hook re-checks that its generation is still current right before it starts, so a hook never runs for a generation you have already switched away from. Generation numbers are allocated above the durable high-water mark, and a generation is published once.

**Updates.** `grip update` writes a lock only when every selected package was checked, none failed and something changed; each package is counted exactly once.

**Rollback.** Every write a rollback makes installs exactly the identity the target generation recorded, from retained bytes only, never inside a published generation, and only over absence or gripsack's own write. A destination counts as restored only when the landed object is that identity. The switch happens only after every destination is settled, with a fresh transaction identifier, and a destination that cannot be restored aborts the rollback before the switch.

These are kernel theorems from [plan 0056](https://github.com/gripsack-dev/gripsack/blob/{release_source}/plan/0056-verified-foundation.md). The proof sources are in [`proofs/`](https://github.com/gripsack-dev/gripsack/tree/{release_source}/proofs) and the kernel in [`crates/gripsack-kernel`](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates/gripsack-kernel).

## What is tested but not yet proved

Everything else on the [safety page](safety.md) is enforced by code and checked by tests, fault injection and a TLA+ model, not by a proof:

- **Crash safety end to end.** Every decision in apply, rollback and recovery is proved; that a crash at any point followed by recovery leaves every destination at its prior or intended identity is crash-injection tested at every step of a run over an in-memory filesystem, and is the next proof, under the storage model below.
- **Directory changes.** When a directory changes shape, the kernel decides when each step runs and that nothing else writes inside it; the steps themselves are host code checked by a TLA+ model and end-to-end tests.
- **Source approval.** Approval binds the exact captured source bundle and policy; evaluation runs in a Deno sandbox with no environment, network or subprocess access.
- **Content integrity.** Downloads are hashed and verified before extraction; the store is sealed read-only and published by rename.

Moving these inward is the roadmap: the crash-safety proofs over the storage model next, then the directory steps themselves.

## What is assumed

The protocol proofs, when they land, rest on a written storage model. These assumptions are stated, fault-tested on an in-memory filesystem that injects crashes, and never proved:

- **S1** `rename` within a directory is atomic and replaces the target; `RENAME_NOREPLACE` and exclusive `mkdir` fail if the name exists; `remove_dir_all` is a sequence of unlinks, not atomic.
- **S2** File data is durable after `fsync(file)`; a name is durable after `fsync(parent)`.
- **S3** Two crash kinds: a *kill* loses nothing already in the page cache, a *power loss* may lose any subset of non-durable operations consistent with completed barriers.
- **S4** One lifecycle writer at a time, held by an advisory lock released when the holder dies.
- **S5** External writers exist and are only *detected*, see below.
- **S6** Two names are the same destination when the filesystem resolves them to the same object. Gripsack detects case-only aliases (as on WSL's `/mnt/c`); names a filesystem treats as equal only after Unicode normalization are not detected.
- **S7** Equal SHA-256 digests mean equal bytes.

Also trusted, as every verified program trusts them: the Rust compiler, the Charon/Aeneas translation, Lean 4 and its kernel, and the Linux kernel.

## What is not claimed

- **The external-writer window.** Between the moment gripsack re-checks a destination and the moment it acts, another process can change it. Every external write gripsack *sees* is preserved; a write inside that window is not. This is a named residual risk, not a solved problem.
- **Effects outside managed files.** Hooks, tasks, services and anything a package's own program does are not transactions. Rollback restores files and launchers; it does not undo a database migration or a command you scheduled.
- **Liveness.** The proofs say what a recovery *may* leave behind, not that it always completes.
- **The world.** Docker Engine, systemd, Deno, Conda channels, registries, the OS and the hardware are outside every proof.
- **Platform.** Linux x86_64 and WSL2 only.

## Why proofs instead of more tests

Gripsack's guarantees used to be documented one review at a time, each with its own model and its own evidence receipt. That did not scale and it was hard to read. Since 0.52 the rule is simple: a guarantee is a theorem over the shipped code, a test that guards behavior you can see, or a bug-finder that has caught a real bug. Anything else goes. A release is the exact source passing its gates, and the proof gate runs alongside the test suites, not as a separate evidence process.
