# Environments

An environment selects packages and command exports for native execution. A profile can expose that same environment to your shell and editor through managed launchers. Neither requires Docker.

## A coherent Conda toolchain

`conda.environment` solves one coherent environment, including its transitive dependencies. This complete workspace exposes ripgrep both to project commands and to a personal profile:

```typescript
import {
  conda, defineWorkspace, environment, pkg, profile, provider,
  targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });
const tools = pkg("tools", {
  producer: provider(conda.environment({
    channels: ["conda-forge"],
    packages: { ripgrep: "*" },
    systemRequirements: {
      libc: { family: "glibc", version: "2.28" },
      linux: "4.18",
    },
  })),
  commands: { rg: "bin/rg" },
  target,
  layout: { kind: "prefix_materialized" },
});
const search = environment("search", { packages: ["tools"], target });
const personal = profile("personal", {
  environment: "search",
  launchers: { directory: "~/.local/bin", commands: ["rg"] },
});

export default defineWorkspace(() => workspace({ outputs: [tools, search, personal] }));
```

```sh
grip update
grip run --env search -- rg --version
grip plan personal
grip apply personal
```

Review and approve the source and changed lock when prompted. `grip run` executes without deploying the personal profile; `grip apply` deploys its explicit launchers through a generation.

Package constraints are Conda MatchSpecs: `"*"`, `"==25.07.1"` for exact equality, `"=25.07"` for a prefix or `">=25.07.1,<26"` for a range. A bare `"25.07.1"` is not a valid constraint. The lock fixes exact archive identities regardless of the authored range.

## Hash-pinned Python wheels

A coherent `conda.environment` can also declare `wheels: [{ name, version, url, sha256 }]` alongside its Conda packages. Use canonical lowercase wheel names, exact versions, explicit HTTPS wheel URLs without credentials/query strings/fragments, and independently approved SHA-256 values. The selected Python runtime and wheel dependencies must already belong to the declared environment; this is not an implicit PyPI solve. Imported Pixi locks can select supported hash-pinned wheel records too.

The core validates metadata, RECORD ownership, dependencies, Python requirements and platform tags. Its pinned helper uses the maintained UV wheel installer offline; original wheel bytes are retained for reconstruction at the actual recipient prefix. Conda/wheel ownership collisions reject rather than overwrite. Binary manylinux wheels require an explicit compatible glibc baseline, checked again on the receiving host.

Native environments must own their non-system runtime libraries. For example, the portable Python/Tk fixture declares `packages: { python: "3.12.*", "xorg-libx11": "*" }` rather than borrowing an undeclared host X11 library. Gripsack reports an incomplete runtime closure instead of silently searching ambient library paths.

Source distributions, editable packages, executable startup files (`.pth`, `sitecustomize`, `usercustomize`) and arbitrary wheel `.data/scripts` are unsupported. Standard metadata-declared console entrypoints are supported. Missing dependencies are not resolved during installation, and package installation scripts are not executed. See [native sharing](sharing.md#conda-and-wheel-reconstruction) for the offline transfer boundary and the [exact SDK reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) for authoring details.

## Solve baselines

`systemRequirements` selects Linux solve virtuals explicitly. Without a declared libc/kernel capability the updater uses measured host facts. The recorded policy is checked on frozen use, alongside actual archive, CPU and runtime admission. A baseline is not a guarantee that every selected archive runs on every distribution.

Keep required libraries in the complete closure. For example, a pyright environment can need an explicit `xorg-libx11` dependency. A successful version command alone does not prove editor, language-server or graphical behavior. Exercise the actual consumer on the host where you deploy it.

Unsupported Conda lifecycle scripts and payload policies fail before publication; importing a lock does not bypass those checks.

## Import a Pixi lock explicitly

Use `pixi.fromLock` when another workflow owns the solve. Capture both the existing manifest and its lock as named inputs, then select the lock's environment. This complete declaration expects a `default` environment exporting ripgrep in those files:

```typescript
import {
  defineWorkspace, environment, inputFile, pixi, pkg, provider,
  targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });
const inputs = [
  inputFile("pixi-manifest", "pixi.toml"),
  inputFile("pixi-lock", "pixi.lock"),
];
const tools = pkg("tools", {
  producer: provider(pixi.fromLock({
    manifest: "pixi-manifest",
    lock: "pixi-lock",
    environment: "default",
  })),
  commands: { rg: "bin/rg" },
  target,
  layout: { kind: "prefix_materialized" },
});
const search = environment("search", { packages: ["tools"], target });

export default defineWorkspace(() => workspace({ inputs, outputs: [tools, search] }));
```

`grip update` imports the selected lock; it does **not** run Pixi, upgrade packages or rewrite `pixi.lock`. To change the solve, update the manifest/lock with your Pixi workflow first, review them, run `grip update`, then review and approve the resulting captured state. Frozen consumers refuse changed imported inputs until that explicit update. Gripsack's import and materialization do not require a `pixi` executable on `PATH`.

## Personal launchers

A profile's `launchers.directory` and `launchers.commands` are explicit. Only uniquely resolved exports from its selected environment become launchers; missing or ambiguous commands fail before mutation. Add the chosen directory to your shell, editor or SSH session's `PATH` yourself. Gripsack does not modify those programs' environments implicitly.

Launchers use the absolute installed core path and retained private state. They re-admit the package/runtime contract on invocation. Keep both available; if the binary moves, restore it or reapply using the replacement core. Do not hand-edit generated launchers.

Use the same UID that owns the state. An explicit `/usr/local/bin` destination does not turn a private store into a multi-user installation; do not make trust records or journals world-accessible.

## Generations and rollback

`grip generations` lists retained generations; `grip rollback` restores a previous managed state, including retained package roots and launcher bindings. It does not re-solve the environment or rebuild packages. Keep recovery data until you have exercised the deployed commands and configuration.

For scoped project execution, use `grip run --env search -- COMMAND` or `grip shell search`. Add [Docker services](services.md) for an explicit project database. For files alongside a toolchain, see [profiles and dotfiles](adopting.md).
