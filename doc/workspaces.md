# Your first workspace

A workspace is one `gripsack.ts` at the root of a repository. It describes the user-space environment you want, not the commands that would build it. This page takes you from nothing to a deployed profile you can roll back.

## Scaffold one

After [installing grip](install.md):

```sh
grip init my-env
cd my-env
grip check
grip plan hello
grip apply hello
```

`init` writes a root `gripsack.ts`, a file-only `hello` profile that deploys under `~/.config/hello/`, sample configuration and editor settings. The first `grip check` asks you to approve the captured source; `grip plan` shows every file that would change; `grip apply` makes generation 1. Replace the sample with the files or packages you actually want.

## Or write it by hand

<!-- example: examples/workspaces/05-first-workspace/gripsack.ts -->
```typescript
import {
  defineWorkspace, file, identity, profile, repoFile, trackedCopyTo, workspace,
} from "@gripsack/core";

const dotfiles = profile("dotfiles", {
  files: [file({
    source: repoFile("config/editor.toml"),
    content: identity(),
    destination: trackedCopyTo("~/.config/editor/config.toml"),
  })],
});

export default defineWorkspace(() => workspace({ outputs: [dotfiles] }));
```

Create `config/editor.toml` next to it. The destination must be outside the repository. No Docker, no package download and no `env.toml` are needed.

```sh
grip check
grip plan dotfiles
grip apply dotfiles
```

`trackedCopyTo` deploys a real file and preserves your later edits rather than overwriting them. If something already lives at the destination, the plan says so and asks for an explicit decision; see [profiles and dotfiles](adopting.md).

## What you can declare

| Output | Purpose | Used by |
|---|---|---|
| `pkg` | A package: a source, a target platform, commands and runtime dependencies | `grip build`, environments, profiles, tasks |
| `environment` | A selection of packages and environment values for one process | `grip run`, `grip shell`, a profile's launchers |
| `profile` | Personal files and launchers, deployed through generations | `grip plan`, `grip apply`, `grip rollback` |
| `service` | A digest-pinned Docker Engine container | `grip up`, `grip down`, `grip services` |
| `task` | A named command graph with prerequisites and postconditions | `grip task run` |
| `check` | A validation command attached to a file, a source or a task | File checks, task postconditions |
| `hook` | A profile lifecycle action | Profile activation |
| `schedule` | A systemd user timer for a task | A profile's `schedules` |

These are ordinary typed values: build them with functions, reuse them, and list every referenced output in `workspace.outputs`. Names are unique; invalid references and cycles are errors at `grip check`.

## Select what you deploy

`grip plan dotfiles` and `grip apply dotfiles` act on that profile only; unselected profiles are neither applied nor pruned. Without a selection, apply processes the declared profile graph. Keep frequently edited configuration in its own profile so the scope of each apply is obvious.

Selection does not narrow approval: you approve the whole captured source, and a change outside the selected profile still needs review.

## The commands, in order

- `grip check` validates declarations. It starts no service and registers no timer.
- `grip update` resolves external sources and frontend pins into `gripsack.lock`. Review the diff; file-only workspaces never need it.
- `grip build NAME` realizes a package without deploying anything personal. A cold `grip apply` does this itself.
- `grip plan` / `grip apply` deploy a profile through a [generation](safety.md#what-apply-does).
- `grip generations` / `grip rollback` list and reselect retained states.

## Where to next

- [Packages](packages.md): a tool from a release archive.
- [Environments](environments.md): a Conda toolchain for `grip run`, with launchers on your path.
- [Profiles and dotfiles](adopting.md): ownership modes and adopting files you already have.
- [Services](services.md), [tasks](tasks.md), [schedules](schedules.md): project plumbing.
- The [SDK reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) and [example workspaces](https://github.com/gripsack-dev/gripsack/tree/{release_source}/examples/workspaces).

Evaluation runs in a sandbox: use `repoFile`, `repoTree` and named `inputFile` declarations for source data instead of reading the filesystem from TypeScript, and expect host facts to arrive through the injected context.
