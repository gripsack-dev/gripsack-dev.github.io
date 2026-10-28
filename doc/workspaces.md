# Workspaces

A workspace describes the user-space environment you want, not a sequence of machine setup commands. Put a root `gripsack.ts` in your repository and export `defineWorkspace(() => workspace({ outputs }))`.

## Create a workspace

After [installing grip](install.md), scaffold a small workspace:

```sh
grip init my-env
cd my-env
grip check
grip plan hello
grip apply hello
```

`init` writes a root `gripsack.ts`, a file-only `hello` profile, captured sample configuration and editor settings. Review the generated files and source approval before applying. Its sample deploys under `~/.config/hello/`; replace it with the files or packages you want. You can also write the complete example below directly without scaffolding.


## Choose your outputs

| Output | Purpose | Use it with |
|---|---|---|
| `pkg` | A named package with a producer, commands and runtime contract | `grip build`, an environment or an image |
| `recipe` | A source build with an explicit toolchain and steps | `grip build` or a package producer |
| `environment` | A process-scoped selection of packages and environment values | `grip run`, `grip shell` or a profile |
| `profile` | Personal files and selected environment launchers | `grip plan`, `grip apply` |
| `image` | Packages and configuration exported as an OCI archive | `grip build` |
| `task` | A manually invoked command graph | `grip task` |
| `check` | An explicit validation command | File validation, build validation or task postconditions |
| `hook` | An explicit profile lifecycle action | Profile activation |

These are ordinary typed values. Reuse a function to produce declarations; include every referenced output in `workspace.outputs`. Names are unique across the catalog. Invalid references and dependency cycles are errors, not an implicit execution order.

## A complete file-only workspace

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

Create `config/editor.toml` with the configuration you want to deploy. The destination must be outside the workspace repository. No Docker, package producer or `env.toml` is needed for this example.

```sh
grip check
grip plan dotfiles
grip apply dotfiles
```

Review the captured source and policy when prompted, then inspect the plan before applying. `trackedCopyTo` deploys a real file and preserves local drift by default. An existing foreign destination needs an explicit ownership decision; see [profiles and dotfiles](adopting.md).

## Select without deploying everything

`grip plan dotfiles` and `grip apply dotfiles` select that profile; they do not apply or prune unselected profiles. With no selection, apply processes the declared profile graph. Keep frequently edited configuration in its own profile to make the deployment scope clear.

Selection is not a trust bypass: approval still covers the exact whole captured source bundle and policy. Changes outside the selected profile remain part of review.

## Separate production, execution and deployment

- [Packages](packages.md) describe how tools are produced and exposed.
- [Environments](environments.md) select tools for project commands without deploying personal files.
- [Profiles](adopting.md) deploy files and launchers through the generation transaction.
- [BuildKit and OCI](builds.md) use packages in source builds and portable image exports.
- [Tasks and checks](tasks.md) make explicit actions and validation discoverable.

`grip update` refreshes external source and frontend/import pins in `gripsack.lock`. Review its diff and approve the changed capture before frozen consumers run. File-only declarations use the approved repository snapshot and need no external package solve.

`grip check` validates declarations; it does not execute recipes or register scheduled jobs. `grip build` realizes outputs without personal activation. A cold `grip apply` realizes required packages before changing destinations; a separate pre-build is optional.

## Authoring and execution

Evaluation runs in provisioned Deno with restricted captured-source reads and no environment, network or subprocess grants. Use `repoFile`, `repoTree` and named `inputFile` declarations for source data instead of evaluation-time filesystem walks. Host facts come from the injected context.

Use the frontend embedded in your installed core, or a deliberately selected matching SDK. See [installation](install.md), [source capture](settings.md) and the [complete SDK reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md). The [workspace examples](https://github.com/gripsack-dev/gripsack/tree/{release_source}/examples/workspaces) show complete repositories, including captured executable files.
