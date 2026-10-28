# Profiles and dotfiles

A profile declares the files and environment launchers you want to deploy. Start with one tool's configuration, keep an independent backup, and review the plan before applying. You can manage dotfiles while leaving packages with your existing OS package manager.

## Choose file ownership

| Destination | Use it for | Boundary |
|---|---|---|
| `symlinkTo(path)` | Store-owned configuration that the application only reads | The destination links to retained read-only content |
| `trackedCopyTo(path)` | Real files the application may rewrite; trees requiring physical sibling layout | Local byte or mode drift is detected and preserved by default |
| `managedBlock(path, marker)` | One delimited section of a shared text file | Gripsack reconciles its block, not the whole file |

Destinations must be normalized absolute or `~/`-prefixed paths outside the workspace repository. They use your privileges, not an implicit elevation mechanism.

## Capture a tree and an executable template

Create `dotfiles/editor/` with your configuration and a captured executable `scripts/editor-theme.sh.tmpl` containing:

```sh
#!/bin/sh
printf '%s\n' '{{ theme }}'
```

Set its executable bit in the repository with `chmod +x scripts/editor-theme.sh.tmpl`. Then declare:

```typescript
import {
  defineWorkspace, file, identity, profile, repoFile, repoTree,
  templateFile, trackedCopyTo, workspace,
} from "@gripsack/core";

const dotfiles = profile("dotfiles", {
  files: [
    file({
      source: repoTree("dotfiles/editor"),
      content: identity(),
      destination: trackedCopyTo("~/.config/editor"),
    }),
    file({
      source: repoFile("scripts/editor-theme.sh.tmpl"),
      content: templateFile({ theme: "dark" }),
      destination: trackedCopyTo("~/.local/bin/editor-theme"),
    }),
  ],
});

export default defineWorkspace(() => workspace({ outputs: [dotfiles] }));
```

`templateFile` renders the captured body once; you do not duplicate it inside TypeScript. Source executability survives rendering. `literalText` has no executable source and produces a 0644 file; `file` has no arbitrary mode option.

`repoTree` can select literal relative prefixes with `include` and `exclude`; these are **not globs**. Each expanded file is owned separately. Foreign siblings are not replaced, and safe internal aliases use captured target bytes. Whole-source capture rejects escapes and cycles before tree selection; use [capture exclusions](settings.md#source-capture) for irrelevant unsafe trees.

## Adopt existing files deliberately

Copy the configuration you want to keep into the workspace source first. Declare its file policy, then run:

```sh
grip check
grip plan dotfiles
grip apply dotfiles
```

For an existing foreign regular file that you deliberately want to manage as a tracked copy, review the explicit takeover plan before authorizing it:

```sh
grip plan dotfiles --take-over
grip apply dotfiles --take-over
```

Keep the selected profile small: takeover is permission over the selected destinations, not a substitute for inspecting them. It is not a general symlink repair or cross-identity ownership transfer. Recorded ownership and unresolved recovery state must be respected; do not erase journals or manifests to force a deployment.

## Guided adoption

From a workspace, `grip adopt` can inventory an existing path, copy its payload into `configs/`, and generate a named profile under `profiles/` plus its root import:

```sh
grip adopt ~/.config/editor --name editor --mode tracked_copy
```

The first invocation deliberately stops with exit status 1 for source review; it does not deploy the destination. Read the generated source, confirm the ownership policy and approve it, then resume:

```sh
grip trust add .
grip adopt ~/.config/editor --name editor --resume
```

Resume uses the approved profile; do not pass `--mode` again. `--yes` skips apply confirmation, not source approval. The interview modes are `tracked_copy` for mutable real files, `owned` for store-owned links, and `merge` for managed text blocks. Keep backups and inspect the plan regardless of which route you choose.


## Drift and retained generations

A tracked copy is user-owned mutable content. If the application changes it, ordinary apply and rollback preserve the drift rather than silently overwrite it. To make that change your new desired state, deliberately copy it back into the repository, review and approve the new captured source, then apply again. `grip update` refreshes external source pins; it does not capture live destination content.

```sh
grip generations
grip rollback
```

Rollback uses retained content without rerendering today's source or rebuilding packages. Keep predecessor generations and prior-state data until the actual application works with the deployed files. Journaled file transitions are not a whole-machine snapshot, and late hook failures do not automatically roll back; see [safety and recovery](safety.md).

## Package artifacts and launchers

`artifactFile` and `artifactTree` select retained package content. Tree deployment still owns individual files, not the destination directory. Use tracked copies for consumers needing real filenames, extensions or sibling resources; per-file store symlinks do not promise those properties.

For command exports, prefer a profile's explicit `environment` and `launchers` declaration rather than maintaining shell wrappers. [Environments](environments.md#personal-launchers) covers PATH, the installed core location and same-UID operation. Attach named [checks](tasks.md#profile-file-checks) when a configuration should be validated before deployment.
