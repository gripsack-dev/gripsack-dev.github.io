# Adopting your dotfiles

Start with a small, reviewable set of files. New configurations should use a
root `gripsack.ts` workspace; the host/module model remains supported as legacy.

## Start with one directory, not your whole setup

Use the [workspace migration guide](workspace-migration.md) and
[persistent environments](environments.md) for current authoring. A file-only
profile needs no package producer or build worker: captured repository files
can become symlinks, tracked copies or managed blocks. Keep a backup of the
original config before starting.

Install core 0.48 and, only if deliberately pinning the SDK, its matching
archive using the [release instructions](https://github.com/gripsack-dev/gripsack/releases/tag/core-v0.48.0).
This is a public **unsigned** release, not an npm or crates.io publication;
the signed installer/updater does not select it. The binary embeds the
frontend and provisions a pinned, SHA-256-verified Deno for evaluation.
Supported hosts are Linux and WSL2 on x86_64.

Approval is for exact captured source and policy, not a one-time blessing of
a directory. Review `grip trust inspect` and the approval prompt; editing
source, changing the SDK pin or refreshing lock inputs can require approval
again. See [source trust](safety.md).

For an existing **legacy** workflow, this still creates a host/module repo:

```bash
grip init my-env && cd my-env
grip check && grip apply
```

It writes `env.toml`, a machine-named host, a `hello` module and editor
configuration. The hello file deploys under `~/.config/hello/`. `grip init`
does not scaffold a workspace; its generated package version is not evidence
of registry availability. Use the embedded frontend or the matching release
SDK archive rather than assuming `npm install` can fetch 0.48.

## Move one real tool over

**Workspace:** copy the intended config into the repository and declare its
profile files with `repoFile` or `repoTree`, `identity()` or `templateFile`,
and a destination such as `trackedCopyTo`. Review source approval and
`grip plan <profile>`, then use `grip apply <profile> --take-over` only after
reviewing every destination the selected profile would take over. Start with
a profile containing just the files you intend to adopt. `grip adopt` does
not edit workspace profiles in 0.48; it refuses that operation explicitly.
The [released SDK reference](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md#captured-files-trees-and-stable-package-roots)
shows captured files and trees without evaluation-time filesystem reads.

**Legacy host/module repo:** `grip adopt` inventories a live path, asks about
ownership, copies the payload into `configs/`, and generates module and host
source. `tracked_copy` is the conservative default; choose `owned` only for
configs the application does not rewrite.

```bash
grip adopt ~/.config/helix
# Review and approve generated source if requested. To resume afterward:
grip adopt ~/.config/helix --resume
```

Generation happens before deployment confirmation: it writes repository
files, not the destination configs. `--yes` skips only apply confirmation,
not source approval. Resume omits `--mode`: the approved module supplies it,
without regenerating source. Takeover is scoped to the requested target;
unrelated destinations do not gain takeover permission.

Legacy adopt records an empty generation 0 on a fresh store. Subsequent
rollback can restore the prior files when their deployed state is intact.
This is not a promise that every workspace starts with that baseline.

## The safety net under all of it

1. **Foreign-path refusal** — deployment refuses foreign destinations unless
   takeover is authorized.
2. **Prior capture** — takeover records original bytes and permission bits
   in the private store.
3. **Drift guards** — tracked-copy and template edits are preserved by
   default. Managed blocks intentionally reconcile their own content; see
   [ownership modes](modules.md#ownership-modes).
4. **Failed transitions** — journaled destination compensation is attempted
   before commit. If the filesystem prevents recovery, the journal blocks
   further mutation; arbitrary commands and external effects are not undone.
5. **Generation rollback** — `grip rollback` returns to a retained generation,
   subject to ownership and drift checks. It does not rebuild current source.
6. **Crash recovery** — durable journals let subsequent mutation recover or
   fail closed. Recovery preserves intervening user edits rather than treating
   them as intact managed output. Late activation failure needs explicit
   recovery; it is not automatic rollback.

Keep the retained generations, prior blobs and private state needed for undo.
Pruning history removes recovery choices; a lockfile alone is not a backup.
Read [the safety contract](safety.md) before relying on rollback.

## The ownership question is the whole game

For each file, ask whether the application rewrites it:

- **Never:** workspace `symlinkTo` (legacy `symlink` / `owned`).
- **Sometimes:** `trackedCopyTo` (legacy `trackedCopy` / `tracked_copy`),
  preserving a real file and detecting drift.
- **Shared text file:** `managedBlock` (legacy `merge`) owns a delimited
  block, not the surrounding text. Use only a format that accepts the markers;
  strict JSON does not accept comments.
- **Per-machine values:** `templateFile` or `templateText`, combined with
  a destination. Legacy `template(to, vars)` computes variables in the host
  entrypoint. Both models can use injected facts rather than ambient reads.

Choose per file, not by application name alone. Templates are rendering, not
a separate promise that an application cannot edit the result.

## What stays outside (on purpose)

Existing system and language package managers can keep managing binaries.
Add workspace packages and environments only when their pinned inputs and
runtime policy are useful to you. Shell state, caches and application-written
state need not enter your profile; adopting a directory does not mean claiming
all future children.

## When it breaks

Use `grip doctor` for runtime and editor wiring, `grip why-owns <path>` for
ownership, and [run logs](runs.md) for diagnostics. Inspect the failed stage
before deciding whether to roll back. Advisory config lint is not a required
workspace check: required checks can block publication or activation.

For an agent-assisted inventory and ownership interview, see
[skills](skills.md). Review its proposed declarations and source approvals;
an agent is not a substitute for the ownership decision or a backup.
