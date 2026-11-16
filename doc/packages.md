# Packages

A package names a producer, a target platform and the commands or artifacts consumers can use. It does not install into a global prefix. Environments, profiles, tasks and images select the same package declarations.

## A release archive

This workspace exposes ripgrep from its upstream static Linux archive:

<!-- example: examples/workspaces/06-release-archive/gripsack.ts -->
```typescript
import {
  defineWorkspace, environment, githubRelease, pkg, provider,
  targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64" });
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

`grip update` resolves the release and records the archive hash in `gripsack.lock`; review that diff and approve the source when prompted. To pin a particular release, set `githubRelease.version` to its exact tag.

The target names only the OS and architecture. Gripsack reads the ABI from each executable: a static binary like this one runs on any Linux x86_64 host, and a dynamically linked one must name the host's platform loader. An `abi` you do declare is checked against the executable, not against the host.

## Locked-release payload paths

Core 0.55.0 and later expand release tokens in package `commands` **values**, `artifactFile` selectors and `artifactTree` include/exclude prefixes. Command names stay stable. For example, this bare-binary release uses one reusable payload pattern for the asset, command and file consumer:

<!-- example: examples/workspaces/17-release-paths/gripsack.ts -->
```typescript
import {
  artifactFile, defineWorkspace, environment, file, githubRelease, identity,
  pkg, profile, provider, targetPlatform, trackedCopyTo, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64" });
const payload = "sops-{version}.{os}.{arch.go}";
const sops = pkg("sops", {
  producer: provider(githubRelease({
    repo: "getsops/sops",
    asset: payload,
  })),
  commands: { sops: payload },
  target,
  layout: { kind: "relocatable" },
});
const secrets = environment("secrets", { packages: ["sops"], target });
const tools = profile("tools", {
  files: [
    file({
      source: artifactFile("sops", payload),
      content: identity(),
      destination: trackedCopyTo("~/.local/bin/sops"),
    }),
  ],
});

export default defineWorkspace(() => workspace({ outputs: [sops, secrets, tools] }));
```

Run `grip update`, then use `grip run --env secrets -- sops --version` or review `grip plan tools` before `grip apply tools`. There is no source `version` pin: a later `grip update` can select a newer release, moving both the command payload and the file consumer without editing this declaration.

`{version}` is the exact locked raw tag; `{version.bare}` strips exactly one leading lowercase `v`. For example, `v1.2.3` becomes `1.2.3`, `vv1.2.3` becomes `v1.2.3`, and `V1.2.3` stays unchanged. Platform tokens are `{os}`, `{arch}`, `{arch.go}`, `{arch.x64}`, `{target}` and `{system}`, with the same meanings as GitHub release asset patterns.

Expansion binds to the referenced package's resolved/locked source, never the current upstream release, a guessed version or another package's lock. Platform tokens have the same Linux x86_64 asset spellings as the fetcher (`{target}` is `x86_64-unknown-linux-musl`, not a dynamic-loader assertion). Payload paths use the exact spelling produced by expansion; there is no asset-search fallback. `grip plan` shows the expanded paths even before package or artifact realization, without fetching payloads.

Core 0.56.0 extends this policy to typed `artifact(output, selector)` references in exec arguments, command environment values, command working directories and environment-level values. A package-subject check's `sourcePath(selector)` uses that subject package's lock. In 0.55, those command/environment selectors were joined literally; only the package exports and profile artifact origins described above expanded.

A required version missing from the referenced source, an unknown token or an unsafe expanded relative path fails with declaration provenance. Expansion happens before filesystem selection; canonical containment is checked even for working directories. `artifact("tool", ".")` still selects the whole artifact. Attached file checks allow only `sourcePath(".")`, not child paths.

Literal argv/env/cwd values and script bodies remain literal: this does **not** mean typed artifact references inside argv stay literal. Command names, destination paths, host/repository paths, input names and writable staging selectors do not acquire release-token expansion. See [typed command selectors](tasks.md#typed-artifact-selectors).

Text plans and JSON `resolved_paths` include typed selectors resolved from admitted lock evidence, without fetching or claiming that a selected path exists. Artifact rows have `kind: "artifact"`, the owning `consumer`, referenced package `output`, concrete payload-relative `selector` and declaration `span`. Retained hooks, launchers and portable environment bindings keep concrete selectors; replay does not reinterpret them against today's lock. Historical literal portable selectors retain their original meaning.

## Roots and layouts

`archiveRoot: { kind: "single_directory" }` selects exactly one real top-level payload directory. Multiple roots, root-level metadata siblings and symlink roots are refused. Commands and `artifactFile`/`artifactTree` selectors are relative to that selected root. This remains the simplest choice for a versioned wrapper directory: select the wrapper once and use paths such as `rg` within it. Use [locked-release payload tokens](#locked-release-payload-paths) when the payload filename or a selected subtree itself carries the version.

Choose the layout that matches the producer:

- `relocatable` for an archive or build result that can run from its retained package root.
- `prefix_materialized` for a coherent Conda or imported Pixi environment whose prefix is materialized by the core.
- `fixed_prefix` with an explicit `prefix` when the package requires that location; an environment selecting it must declare the matching prefix.

## Runtime dependencies are part of the package

Declare required package edges with `runtime: ["runtime-package"]`. The executable's ABI selects its loader; it does not grant arbitrary host library access. Keep libraries and sibling resources in the retained closure when the tool needs them.

A Linux GNU package can explicitly opt into reviewed host libraries with `hostRuntime: { libraryDirectories: ["/opt/vendor/lib64"] }`. Those directories remain mutable trusted host inputs, not portable package content. See [runtime safety](safety.md#host-libraries-and-launchers).

Some tools locate resources through their resolved executable pathname. A managed launcher does not promise the original `/proc/self/exe` pathname. For tools requiring a real sibling tree, use an explicit tracked-copy deployment and captured executable wrapper rather than assuming a launcher can repair the upstream layout. [File policies](adopting.md#choose-file-ownership) explain the difference.

## More producers and consumers

- [Native Conda and explicit Pixi imports](environments.md)
- [Sources, authentication and lock updates](fetchers.md)
- [Managed launchers](environments.md#personal-launchers)
- [Native artifact sharing](sharing.md)
- [SDK package contracts](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md)
