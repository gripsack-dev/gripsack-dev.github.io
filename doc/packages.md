# Packages

A package names a producer, a target platform and the commands or artifacts consumers can use. It does not install into a global prefix. Environments, profiles, tasks and images select the same package declarations.

## A release archive

This workspace exposes ripgrep from its upstream Linux musl archive:

```typescript
import {
  defineWorkspace, environment, githubRelease, pkg, provider,
  targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "musl" });
const ripgrep = pkg("ripgrep", {
  producer: provider(githubRelease({
    repo: "BurntSushi/ripgrep",
    asset: "ripgrep-{version.bare}-x86_64-unknown-linux-musl.tar.gz",
  })),
  archiveRoot: { kind: "single_directory" },
  commands: { rg: "rg" },
  target,
  layout: { kind: "relocatable" },
});
const search = environment("search", { packages: ["ripgrep"], target });

export default defineWorkspace(() => workspace({ outputs: [ripgrep, search] }));
```

```sh
grip update
grip build ripgrep
grip run --env search -- rg --version
```

Review source approval prompts and the lockfile change between commands. `update` fixes the resolved release and archive identity; later consumers use those pins. This is an authoring example, not a promise about every upstream release or host. To request a particular release, set `githubRelease.version` to its exact tag.

## Roots and layouts

`archiveRoot: { kind: "single_directory" }` selects exactly one real top-level payload directory. Multiple roots, root-level metadata siblings and symlink roots are refused. Commands and `artifactFile`/`artifactTree` selectors are literal paths relative to that selected root: version placeholders belong in source asset patterns, not selectors.

Choose the layout that matches the producer:

- `relocatable` for an archive or build result that can run from its retained package root.
- `prefix_materialized` for a coherent Conda or imported Pixi environment whose prefix is materialized by the core.
- `fixed_prefix` with an explicit `prefix` when the package requires that location; an environment selecting it must declare the matching prefix.

Native provider packages need no synthetic recipe or build worker. The former source-recipe backend is [retired](builds.md).

## Runtime dependencies are part of the package

Declare required package edges with `runtime: ["runtime-package"]`. A selected ABI identifies compatibility and loader behavior; it does not grant arbitrary host library access. Keep libraries and sibling resources in the retained closure when the tool needs them.

A Linux GNU package can explicitly opt into reviewed host libraries with `hostRuntime: { libraryDirectories: ["/opt/vendor/lib64"] }`. Those directories remain mutable trusted host inputs, not portable package content. See [runtime safety](safety.md#host-runtime-dependencies).

Some tools locate resources through their resolved executable pathname. A managed launcher does not promise the original `/proc/self/exe` pathname. For tools requiring a real sibling tree, use an explicit tracked-copy deployment and captured executable wrapper rather than assuming a launcher can repair the upstream layout. [File policies](adopting.md#choose-file-ownership) explain the difference.

## More producers and consumers

- [Native Conda and explicit Pixi imports](environments.md)
- [Sources, authentication and lock updates](fetchers.md)
- [Managed launchers](environments.md#personal-launchers)
- [Native artifact sharing](sharing.md)
- [SDK package contracts](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md)
