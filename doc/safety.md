# Safety and recovery

Gripsack writes to files you care about, so this page is about what happens to them: how an apply is structured, what a crash leaves behind, how ownership and drift are decided, and what you still have to do yourself. For what is formally proved versus assumed, see [how gripsack stays safe](guarantees.md).

Two things first. It is alpha software: keep an independent backup of anything irreplaceable. And generations protect *managed files and launchers*; they do not undo what your hooks, tasks, services or the tools themselves do.

## What apply does

{anim:apply}

1. **Realize packages** into the read-only store. Content is verified, sealed read-only and published by rename, so a half-downloaded archive never becomes a package. Because published entries are read-only, a tool running from the store cannot modify it; Python can no longer write `__pycache__` into a package and break the next apply.
2. **Journal** a durable run marker. For each destination, record its prior state and intended change durably before changing that destination.
3. **Write that destination** after a final re-check through a pinned directory handle. If it no longer matches the observation used for the write, stop rather than overwrite it. Repeat the journal-and-write sequence for the next destination.
4. **Run pre-flip checks** you attached to files, still inside the transaction.
5. **Flip `current`**: one atomic rename selects the new generation. This is the commit point.
6. **Run hooks** (`post_link`, `post_activate`). Hook failures are reported; they never roll the committed generation back.

Destination writes are not atomic across a whole profile: a program reading its config in the middle of step 3 can see the new file before its sibling. Stop consumers that need an uninterrupted view.

## What a crash leaves behind

{anim:crash}

Before starting another lifecycle mutation, gripsack classifies the interrupted transaction. It compares the `current` selection with the previous and target selections in the journal, including their transaction identities:

- **Uncommitted** (`current` is still the previous selection, or there was no previous selection and there is no `current`): recover prior state from the journal where the destination can be restored safely.
- **Committed** (`current` matches the target selection): the switch landed. Finish cleanup and handle pending activation under its recorded intent.
- **Ambiguous** (neither): stop rather than guessing. Corrupt manifests and quarantined journal entries are reported, not treated as disposable.

Recovery checks file bytes, Unix modes and symlink targets, not mtimes, ownership or extended attributes. It leaves an outside edit it detects alone rather than replacing it with the snapshot. Crash-injection tests check prior and intended identities after interruptions; they do not rule out a concurrent edit racing the final re-check on a real filesystem.

Do not delete journals, manifests or managed files to "unstick" a refusal; the [run log](runs.md) says what recovery found.

## Ownership and drift

{anim:ownership}

Every destination has an owner. Gripsack writes only when the destination is absent, or holds exactly what gripsack wrote last time. Two other cases are decided conservatively:

- **Drift.** A `trackedCopyTo` file that the application (or you) changed since the last apply is *yours*. Apply and rollback both leave it alone and say so. To adopt the change, copy it back into the repository, review and apply.
- **Foreign files.** A file gripsack never wrote is refused. `grip plan --take-over` shows what adoption would do; `grip apply --take-over` journals the prior bytes and adopts the selected destinations only. It is not a general ownership transfer and does not cross workspaces.

`symlinkTo` links the destination to read-only store content; `managedBlock` reconciles one delimited section of a shared text file and leaves every byte outside the markers alone. See [profiles and dotfiles](adopting.md) for choosing between them.

**When a file becomes a directory.** Inside a tree with a directory receipt, an unchanged managed file with no prior to restore can grow children: `plan` leaves the file alone, `apply` replaces it with the directory, and rolling back to the earlier generation restores the file. This does **not** apply to a taken-over file with a recorded prior, or to a blocking file Gripsack never managed. In either case `plan` and `apply` refuse before changing the deployed files or selecting a generation. Use a different destination for the child rather than trying to force the takeover.

## Rollback, retention and GC

```sh
grip generations
grip rollback
grip gc --dry-run
```

`grip rollback` reselects a retained generation: files, launchers and package roots come from retained bytes, nothing is re-solved or rebuilt, and drift is preserved exactly as during apply. Rollback is a new activation and may run the retained generation's hooks; it is not an undo of commands run since then.

`grip gc` refuses while recovery or activation is pending, or if `current` names a missing generation. It never removes the current generation or anything a retained generation or recovery root references. `keep_generations` in [settings](settings/reference.md) controls retention; keep predecessors until the real application has worked with the deployed files.

## Trust and review

There is no approval step. Workspace code is evaluated in a sandboxed Deno with no environment, network or subprocess access, over a captured copy of the repository. Editing a file in your own repository never invalidates anything.

- **Local repositories are trusted.** Running `grip` on a repository on your disk is consent.
- **A remote repository is trusted on first use.** `grip ... --repo <git url>` asks once per origin URL, showing what the repository declares. Later commits from the same origin do not ask again. Spellings of one origin (trailing slash, `.git`, embedded credentials) are one record.
- **The plan is the guardrail.** `grip plan` lists what is new since the last apply of that repository: hook bodies, fetch domains and destinations outside `~`. `grip apply` shows the same list and asks for confirmation on a terminal, but only when such items are new. Without a terminal it refuses unless you pass `--yes`.

```sh
grip trust list
grip trust remove https://example.com/me/env.git
```

`grip trust list` shows the remote origins trusted on first use; `grip trust remove <url>` forgets one, and its next use asks again. The record of what you have already seen is a convenience: deleting it only makes every item new again, and it never gates evaluation.

The global `--yes` (`-y`) answers every confirmation for scripts and CI: it trusts a remote on first use and applies new items. Use it where the repository and its reviewers are the control, not as a habit at a terminal.

Confirming says nothing about what the packages and hooks you declared will do when they run: those run with your privileges. Old `trust.toml` files are ignored, and `grip trust add` and `grip trust inspect` no longer exist.

A CI job needs no approval step:

```sh
set -eu
grip check
grip plan
```

## Hooks and checks

Rendered-file checks run before any destination is written. Deployed `pre_flip` checks run after candidate writes but before the flip, inside the transaction. `post_link` and `post_activate` run after commit and are never auto-rolled back.

Hooks have durable intents. An interrupted delivery can run again under the same intent id, so write idempotent hooks. Failed intents are not retried automatically. See [tasks and checks](tasks.md).

## Host libraries and launchers

A Linux GNU package may declare `hostRuntime: { libraryDirectories: [...] }`. Those directories are trusted host input: review who controls them. They are package-scoped and never widen what the evaluator or other packages can see.

Each time a launcher runs, it checks only the command being run against its sealed, hash-addressed payload, and refuses a tampered executable. It no longer re-hashes every package or walks every file, which makes an exec of a 30-package environment about three times faster (roughly 190 ms to 55 ms). The rest of a payload is covered by `grip store-verify`, which detects tampering anywhere in a retained payload; `grip store-verify --repair` removes corrupt paths so the next apply fetches them again. `grip gc` and repair also remove sealed read-only trees.

Managed launchers embed the absolute path of the installed core and its private state directory. If you move the binary, reapply with the new one rather than editing launchers. Run as the UID that owns the state; placing a launcher in `/usr/local/bin` does not make the store multi-user.

## What is not covered

- Effects of hooks, tasks, services and the programs you deploy. Rollback does not undo a database migration.
- Writes by another process in the window between gripsack's re-check and its own write ([a named residual risk](guarantees.md#what-is-not-claimed)).
- Same-UID or privileged tampering with the store, journals or trust records. `grip store-verify` can find tampering in a payload after the fact; it does not prevent it.
- Anything outside Linux x86_64 and WSL2.
