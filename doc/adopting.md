# Profiles and dotfiles

A profile declares the files and environment launchers you want to deploy. Start with one tool's configuration, keep an independent backup, and review the plan before applying. You can manage dotfiles while leaving packages with your existing OS package manager.

## Choose file ownership

| Destination | Use it for | Boundary |
|---|---|---|
| `symlinkTo(path)` | Store-owned configuration that the application only reads | The destination links to retained read-only content |
| `trackedCopyTo(path)` | Real files the application may rewrite; trees requiring physical sibling layout | Local byte or mode drift is detected and preserved by default |
| `managedBlock(path, marker)` | One delimited section of a shared text file | Gripsack reconciles its block, not the whole file |

{diagram:ownership|Decision tree: for a destination, if nothing is live gripsack writes; if the last file gripsack wrote is live it updates; if gripsack's file changed since it preserves the drift; if a file gripsack never wrote is live it refuses unless --take-over adopts it. Three ownership modes: symlinkTo, trackedCopyTo, managedBlock.|What happens to whatever is already at a destination.|tall}

Destinations must be normalized absolute or `~/`-prefixed paths outside the workspace repository. They use your privileges, not an implicit elevation mechanism.

## Capture a tree and an executable template

Create `dotfiles/editor/` with your configuration and a captured executable `scripts/editor-theme.sh.tmpl` containing:

```sh
#!/bin/sh
printf '%s\n' '{{ theme }}'
```

Set its executable bit in the repository with `chmod +x scripts/editor-theme.sh.tmpl`. Then declare:

<!-- example: examples/workspaces/09-dotfile-tree/gripsack.ts -->
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

For `repoTree`, `inputDirectory` and `artifactTree`, use `include: ["bin"]` to select `bin` and its descendants, not `binary`; `exclude: ["bin/debug"]` removes that subtree. Neither list accepts `*`, `?`, bracket classes or brace alternatives. Only artifact selectors accept the [locked release and platform placeholders](#package-artifacts-and-launchers) described below.

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

The first invocation deliberately stops with exit status 1 for review; it does not deploy the destination. Read the generated source and confirm the ownership policy, then resume:

```sh
grip adopt ~/.config/editor --name editor --resume
```

To abandon before resuming, remove only the generated paths listed by the attempt. Keep `gripsack.ts`. Since 0.56.1, if adoption edited the workspace, it names the import and the entry in `outputs` to remove. If it prints a manual-integration snippet instead, it did not edit the workspace.

Resume uses the generated profile; do not pass `--mode` again. `--yes` answers the apply confirmation for scripts. The interview modes are `tracked_copy` for mutable real files, `owned` for store-owned links, and `merge` for managed text blocks. Keep backups and inspect the plan regardless of which route you choose.


## Drift and retained generations

A tracked copy is user-owned mutable content. If the application changes it, ordinary apply and rollback preserve the drift rather than silently overwrite it. To make that change your new desired state, deliberately copy it back into the repository, review it, then apply again. `grip update` refreshes external source pins; it does not capture live destination content.

```sh
grip generations
grip rollback
```

Rollback uses retained content without re-rendering today's source or rebuilding packages. Keep predecessor generations until the real application works with the deployed files. See [safety and recovery](safety.md) for the full ownership and drift rules, with a diagram.

## Package artifacts and launchers

`artifactFile` and `artifactTree` select retained package content. Tree deployment still owns individual files, not the destination directory. Use tracked copies for consumers needing real filenames, extensions or sibling resources; per-file store symlinks do not promise those properties.

Since 0.59, `symlinkTo(artifactFile(...))` over an `artifactFile` or `artifactTree` selector links into the realized package instead of publishing a copy, and the generation keeps that package retained. Prefix-relative programs and `$ORIGIN` rpaths keep working, which is what makes conda `tmux` and `helix` usable this way. A tracked copy still copies.

In core 0.55.0 and later, `artifactFile` selectors and `artifactTree` include/exclude prefixes accept `{version}`, `{version.bare}`, `{os}`, `{arch}`, `{arch.go}`, `{arch.x64}`, `{target}` and `{system}`. They use the referenced package's resolved/locked source, with the same platform spellings as the release asset. `{version}` preserves the raw tag; `{version.bare}` strips exactly one leading lowercase `v`. With no source `version` pin, `grip update` can move these consumers to the newly locked release without editing your profile.

For example, within a `file` declaration, select a version-bearing subtree with:

```typescript
source: artifactTree("tool", {
  include: ["tool-{version.bare}/share"],
  exclude: ["tool-{version.bare}/share/cache"],
}),
```

These are **segment-prefix selectors, not globs**: an expanded `tool-1.2.3/share` selects that path and its descendants, not `tool-1.2.3/shared`. Include and exclude both expand before selection. Paths are relative to the package root, including any `archiveRoot` selection; do not repeat a wrapper already removed by `single_directory`.

`grip plan` shows expanded paths even before package or artifact realization, without fetching payloads or claiming path existence. Missing required source versions, unknown tokens and unsafe expanded relative paths fail with declaration provenance. No release-token expansion happens in destination paths, `repoFile`/`repoTree` selectors, command names, literal argv/env/cwd values or script bodies. Since 0.56, typed `artifact` references in hook and check commands **do** expand, including arguments, environment values and working directories; package-subject `sourcePath` references use the subject's locked source. Attached file checks still accept only `sourcePath(".")`. See [typed command selectors](tasks.md#typed-artifact-selectors) and the [complete bare-binary package and file consumer](packages.md#locked-release-payload-paths).

For command exports, prefer a profile's explicit `environment` and `launchers` declaration rather than maintaining shell wrappers. [Environments](environments.md#personal-launchers) covers PATH, the installed core location and same-UID operation. Attach named [checks](tasks.md#profile-file-checks) when a configuration should be validated before deployment.
