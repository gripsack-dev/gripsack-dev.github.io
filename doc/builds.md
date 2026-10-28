# BuildKit and OCI images

Build source into a retained package, run it natively, or export the same package as an OCI image. Gripsack owns the declarations, input identities and native store; BuildKit performs isolated Linux production and OCI export.

## Prerequisites

- A supported Linux x86_64 or WSL2 host with `grip` installed.
- Docker installed, running and accessible to your user. In WSL2, enable access to a Linux Docker daemon in the distribution you use.
- Access to the declared digest-pinned toolchain image and the worker/helper artifacts on a cold build. Review registry access and Docker privileges separately from source approval.
- A complete source tree, including dependency bytes needed by an offline build.

The core lazily provisions its pinned, hash-verified bridge helper and starts its owned worker when production needs them. There is no separate `builder start` step. An operator can deliberately select a helper with `grip build --bridge PATH`; a repository cannot choose that executable. Source-built cores need a matching helper artifact or override until matching release assets are available.

File-only profiles, native provider packages and already-retained outputs do not need a worker. `grip check` never starts one.

## Source builds

Create `source/greeter.c`:

```c
#include <stdio.h>

int main(void) {
    puts("hello from gripsack");
    return 0;
}
```

Save this complete workspace as `gripsack.ts`. It uses the pinned toolchain from the project's [source-build example](https://github.com/gripsack-dev/gripsack/blob/{release_source}/examples/workspaces/03-source-built/gripsack.ts):

```typescript
import {
  defineWorkspace, environment, exec, fileFetch, image, lit, outputPath,
  packageCommand, pkg, recipe, sourcePath, targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });
const build = recipe("build-greeter", {
  source: fileFetch("source"),
  execution: {
    kind: "isolated_linux",
    worker: "buildkit",
    platform: target,
    toolchain: {
      reference: "docker.io/library/golang@sha256:e3665e241a474aba30bbfaf177cfa88e1913e970c83bd86889cacfb67d6e7e51",
    },
  },
  output_kind: "tree",
  target,
  steps: [
    exec({ argv: [lit("mkdir"), lit("-p"), outputPath("bin")] }),
    exec({ argv: [
      lit("cc"), lit("-static"), sourcePath("greeter.c"),
      lit("-o"), outputPath("bin/greeter"),
    ] }),
  ],
});
const greeter = pkg("greeter", {
  producer: "build-greeter",
  commands: { greet: "bin/greeter" },
  target,
  layout: { kind: "relocatable" },
});
const dev = environment("dev", { packages: ["greeter"], target });
const container = image("greeter-image", {
  packages: ["greeter"],
  target,
  config: { entrypoint: [packageCommand("greeter", "greet")] },
});

export default defineWorkspace(() => workspace({
  outputs: [build, greeter, dev, container],
}));
```

```sh
grip check
grip update
grip build greeter --json
grip run --env dev -- greet
```

Review source and lock approval when prompted. `sourcePath` binds immutable captured input; `outputPath` binds writable output staging. These typed paths avoid embedding machine-specific paths in the recipe. The static link in this example makes the tiny program self-contained; arbitrary dynamically linked programs need a complete runtime closure.

Builds do not activate a personal profile. Required recipe checks gate publication; a published package belongs to the native store, not the worker's disposable cache.

## OCI images

The workspace above also declares `greeter-image`. Export it with:

```sh
grip build greeter-image --json
```

The returned image path names a retained **OCI archive**, not a running container and not a registry push. Import or copy that archive using an OCI-capable tool in your deployment workflow. For example, with Skopeo installed, set `archive` to the returned image path and copy it into a local Docker daemon:

```sh
: "${archive:?set this to the image archive path returned by grip build}"
skopeo copy "oci-archive:$archive" docker-daemon:gripsack-greeter:local
docker run --rm --read-only --network none gripsack-greeter:local
```

This example uses scratch because no `base` is declared. An explicit base must be digest-pinned and does not contribute inherited runtime configuration. Declare your own `config.entrypoint`, `args`, `env`, absolute `cwd` and numeric `user: { uid, gid }` as needed.

Packages default to `/opt/gripsack/<name>`. `destinations` can declare explicit paths and numeric owners. Overlapping placements and leftover base files inside package prefixes are refused. Host-runtime library declarations do not copy those host libraries into images; host-coupled packages are refused for portable image placement.

Before publication, native admission checks archive descriptors, hashes, layer identities, platform/configuration and selected package bytes, links, modes and ownership, including cache hits. An admitted archive still needs application-level testing in your chosen container runtime.

## Rust packages

`cargoPackage(name, spec)` returns a recipe/package pair to spread into `workspace.outputs`. Supply captured source with `Cargo.lock`, vendored dependencies and `.cargo/config.toml`; the lockfile alone is not dependency bytes. Select a digest-pinned Rust toolchain with native linker tools, an explicit Linux GNU or musl target, and a mapping from command names to Cargo binary targets.

The helper runs release tests/builds with `--frozen --offline`, installs only the named binaries and removes intermediate build output before export. See the [SDK cargoPackage contract](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) for the complete declaration.

## Worker lifecycle and limits

```sh
grip builder status
grip builder stop
grip builder cache-clean
```

`status` observes without starting a worker. Stop/cleanup refuse active clients. `cache-clean` removes the owned worker's disposable cache, not retained native artifacts. Use `grip gc --dry-run` to inspect native retention separately.

`grip build` supports `--builder-cpus`, `--builder-memory-mib` and `--timeout-seconds`; the deadline covers helper preparation, execution and cleanup. The supported production worker is Linux x86_64 with Docker. Host recipe execution and scheduled execution are not available; declaring them does not grant execution. See [tasks](tasks.md) for explicit manual actions and [safety](safety.md) for trust boundaries.
