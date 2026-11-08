# How gripsack stays safe

Gripsack changes files you care about. This page says exactly what protects them: what is proved, what is tested, what is assumed and what is not claimed. If a sentence here is not true of the released code, it is a bug.

## The idea: rings

The code is arranged in rings. The center holds pure decisions over typed data with no IO at all. Each ring outward holds less trusted code and is checked in a cheaper way, and it trusts only the rings inside it. Code moves *inward* to gain a guarantee; nothing is modelled on the outside.

{diagram:rings|Nested rings: Product, Edge, Host, Protocol and Kernel. The kernel's proved decisions flow to a Lean proof project over the shipped Rust; the host's storage assumptions point to the unproved world.|The rings as of 0.52. Purple is proved, red is the next proof target, the rest is tested.}

| Ring | What lives there | How it is checked |
|---|---|---|
| **Kernel** | Pure decisions: which generation is committed, what GC may delete, in what order a journal record becomes durable | **Proved in Lean 4** over a translation of the shipped Rust |
| **Protocol** | Apply, rollback, recover and GC as state machines that observe, decide and issue one command at a time | Today: crash-injection tests and model checking. Next: Lean proofs under the storage assumptions below |
| **Host** | The driver loop, filesystem access, store layout, locks | Small enough to read; every assumption listed; fault injection and crash tests |
| **Edge** | TypeScript evaluation, downloads, archives, Conda, Docker, systemd | Sandbox, typed admission, hash-verified bytes, fuzzing |
| **Product** | The CLI, review, adopt, doctor | End-to-end flows against the real binary |

## What is proved today (0.52)

The kernel is a dependency-free Rust crate, `gripsack-kernel`. The `proofs` release gate translates it to Lean 4 with [Charon and Aeneas](https://github.com/AeneasVerif/aeneas) and proves 34 theorems over that translation. There is no hand-written Lean copy of the Rust: the proofs are about the bytes that ship. The gate also checks that every theorem uses only Lean's three standard axioms (`propext`, `Classical.choice`, `Quot.sound`) and that each of fourteen deliberately broken variants of the Rust fails exactly the theorem that should catch it.

**Commit classification.** After an interruption, the next command looks at three generation identities: `current`, the recorded `previous` and the recorded `target` of the interrupted transaction.

- *Committed* if and only if `current` equals `target`.
- *Uncommitted* if and only if the run was fresh with no `current`, or `current` equals `previous` and not `target`.
- *Ambiguous* otherwise, which stops every further mutation until you look.

A higher generation number never grants commit authority; only identity does. Each transaction carries a 32-byte identifier compared byte for byte.

**Garbage collection.** `grip gc` may proceed only when no recovery is pending and `current` names a generation in the inventory. Pruning selects exactly the oldest generations beyond your `keep_generations`, in order, never the current one and never anything newer than the cut. Deletion removes a candidate only if no root names it. Generation inventories are admitted only when strictly ascending.

**Journal publication.** A journal record becomes durable through exactly one order: stage, sync the file, publish the name, sync the directory. `finish` yields a durable record only when that sequence completed, and a mutation is authorized only by a durable run marker *and* a durable entry, never one alone.

These are the first three of the kernel theorems planned in [plan 0056](https://github.com/gripsack-dev/gripsack/blob/{release_source}/plan/0056-verified-foundation.md). The proof sources are in [`proofs/`](https://github.com/gripsack-dev/gripsack/tree/{release_source}/proofs) and the kernel in [`crates/gripsack-kernel`](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates/gripsack-kernel).

## What is tested but not yet proved

Everything else on the [safety page](safety.md) is enforced by code and checked by tests, fault injection and a TLA+ model, not by a proof:

- **Ownership and drift.** A tracked copy that you changed is preserved; a file gripsack never wrote is refused unless you pass `--take-over`; a managed block touches only the bytes between its markers.
- **Crash recovery as a whole.** Prior state and intent are journaled before any destination write; the flip is one atomic rename; recovery restores prior bytes or finishes activation. The *classification* step inside it is proved; the surrounding machine is the next proof target.
- **Generation identity.** New generation numbers exceed the durable high-water mark; published generations are immutable.
- **Source approval.** Approval binds the exact captured source bundle and policy; evaluation runs in a Deno sandbox with no environment, network or subprocess access.
- **Content integrity.** Downloads are hashed and verified before extraction; the store is sealed read-only and published by rename.

Moving these inward, in roughly this order, is the roadmap: ownership and drift decisions and the managed-block splice first, then the protocol machines.

## What is assumed

The protocol proofs, when they land, rest on a written storage model. These assumptions are stated, fault-tested on an in-memory filesystem that injects crashes, and never proved:

- **S1** `rename` within a directory is atomic and replaces the target; `RENAME_NOREPLACE` and exclusive `mkdir` fail if the name exists; `remove_dir_all` is a sequence of unlinks, not atomic.
- **S2** File data is durable after `fsync(file)`; a name is durable after `fsync(parent)`.
- **S3** Two crash kinds: a *kill* loses nothing already in the page cache, a *power loss* may lose any subset of non-durable operations consistent with completed barriers.
- **S4** One lifecycle writer at a time, held by an advisory lock released when the holder dies.
- **S5** External writers exist and are only *detected*, see below.
- **S6** The filesystem distinguishes names at least as finely as gripsack does. A case-insensitive mount such as WSL's `/mnt/c` violates this today.
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
