# Workspace migration

The module model — `env.toml`, `hosts/*.ts`, `modules/*.ts` — is
**legacy: supported, with no removal date**. The workspace (one root
`gripsack.ts`) is the active development surface. This page is where
the SDK's `pixi(package)` diagnostic sends you, and the honest mapping
for moving a repo across — including what you should *not* move yet.

## Where the two models stand

| model | entrypoint | status |
|---|---|---|
| modules | `env.toml` + `hosts/<name>.ts` selecting `modules/*.ts` | legacy — fully supported: source readers, `grip apply`, hooks through the legacy activation ledger |
| workspace | one root `gripsack.ts` | the active development surface |

`grip apply --help` labels the host/module model "legacy". That word
is a direction of travel, not a countdown: **no removal date is set**.
A module repo that does everything you need has no obligation to move.
New capability — coherent Conda/Pixi environments, executing profile
hooks, platform-keyed locks — lands as workspace outputs.

## What maps to what

| in the module repo | in the workspace |
|---|---|
| `hosts/<name>.ts` — one entrypoint per machine, `defineEnv((ctx) => …)` | one `gripsack.ts`; the same `ctx` facts gate outputs and falsy entries drop out |
| per-host parameters (template vars computed from `ctx.facts`) | per-output `targetPlatform({ os, arch, abi })` plus values computed in the entrypoint |
| per-host binary destinations in module `install` | profile file destinations — `symlinkTo` / `trackedCopyTo` / `managedBlock` |
| `locks/<host>.lock` — one lockfile per host | one platform-keyed `gripsack.lock` |
| ownership modes `symlink` / `trackedCopy` / `merge` / `template` | `symlinkTo` / `trackedCopyTo` / `managedBlock` / `templateText` — semantics unchanged |
| `pixi(package)` provider | `conda.environment(...)` or `pixi.fromLock(...)` — below |

Config ownership is unchanged between the models: store-owned
symlinks, drift-preserving tracked copies, delimited managed blocks,
rendered templates — the same table as
[ownership modes](modules.md#ownership-modes). What changes is the
declaring file, not the contract, so an adoption decision made once
carries over.

## Removed: `pixi(package)`

The old callable `pixi("name", { … })` constructor was removed in
0.44. Calling the public `pixi` binding now throws a structured E130
diagnostic — not a bare `TypeError` — naming the removal, the
replacements and this page:

```text
pixi(package) was removed in 0.44; a coherent environment belongs in a gripsack.ts workspace
  help: Use conda.environment(...) or pixi.fromLock(...).
        Migration guide: https://gripsack.dev/docs/workspace-migration.html
```

A package stops being one fetched thing and becomes a coherent
environment output. Solve it natively:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts — conda.environment</span></div>
<pre><code class="language-typescript">import { conda, pkg, provider, targetPlatform } from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });

export const node = pkg("node", {
  producer: provider(conda.environment({
    channels: ["conda-forge"],
    packages: { nodejs: "=26.10.0" },
  })),
  commands: { node: "bin/node" },
  target,
  layout: { kind: "prefix_materialized" },
});
// … an environment("tools", …) output selects packages; a
// profile("with-node", …) output deploys the environment and any
// config files — see below.
</code></pre>
</div>

The complete verified shape — environment and profile wired up,
applied and sourced — is
[persistent environments](environments.md#a-profile-with-a-real-toolchain).

…or freeze exactly what you reviewed as a Pixi lock. The manifest and
lock are captured repository files, declared as named workspace inputs
— never host paths:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts — pixi.fromLock</span></div>
<pre><code class="language-typescript">import { inputFile, pixi, provider } from "@gripsack/core";

// captured repository files become named inputs…
const inputs = [
  inputFile("pixi-manifest", "pixi.toml"),
  inputFile("pixi-lock", "pixi.lock"),
];

// …and the frozen import selects a lock environment by name
const pyrightSource = provider(pixi.fromLock({
  manifest: "pixi-manifest",
  lock: "pixi-lock",
  environment: "default",
}));
// pass `inputs` to workspace({ inputs, outputs: [/* … */] }) and use
// the source as pkg("pyright", { producer: pyrightSource, /* … */ })</code></pre>
</div>

A changed manifest or lock document is refused until an explicit
`grip update` and renewed exact-digest source approval — between
updates as well. To pin a cross-host libc baseline, declare it in the
manifest (`[system-requirements]`) — see
[solve baselines](environments.md#solve-baselines).

## Lockfiles

Legacy resolution pins one `locks/<host>.lock` per host: N machines,
N lockfiles, each resolved on its own host. A workspace writes **one
platform-keyed `gripsack.lock`**: per platform it records immutable
exact archives plus the solve's recorded assumptions. Identity is not
portability — before reusing or re-solving a lock across hosts, read
[solve baselines](environments.md#solve-baselines).

## Running both during migration

Nothing forces a flag day:

- Module entrypoints keep working — module repos remain supported
  (readers, `grip apply`, hooks through the legacy activation ledger).
- Add `gripsack.ts` at the repo root; the workspace path reads it
  without a host shim.
- Move host by host, tool by tool. The module examples and the
  workspace coexist while you migrate.
- Ownership decisions carry over unchanged — no per-file re-decision.

## Downgrade boundary

Measured 2026-10-06 with real binaries and completed applies (all
transactions finished): grip 0.44.1 applied, then grip 0.42.0 against
the finished state.

| completed state left by a 0.44/0.45 apply | grip 0.42.0 `gc` | grip 0.42.0 `rollback` |
|---|---|---|
| legacy module-repo generation | collected | restored generation 1 exactly; destination bytes correct |
| workspace profile, files only | collected | restored |
| workspace profile with a structured environment contribution | refused: "manifest is corrupt — refusing to collect: unknown field `kind` …" | nothing to roll back (exit 1) |
| generation manifest in the 0.45 workspace-hook v2 envelope | rejected by old readers before effects, by design | — |

`grip status` does not exist in 0.42.0 (exit 2). Every refusal above
fails closed — nothing is misread, no wrong effects run. In short:
after a completed 0.44/0.45 apply, 0.42.0 can still operate on legacy
and file-only generations; it cannot operate on generations with
structured environment records or workspace hooks. Downgrading past
those generation shapes is unsupported — upgrade back or keep the
newer binary.
