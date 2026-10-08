# Workspace migration

The module model — `env.toml`, `hosts/*.ts`, `modules/*.ts` — is
**legacy: supported, with no removal date**. The workspace (one root
`gripsack.ts`) is the active development surface. This page is where
the SDK's `pixi(package)` diagnostic sends you, and the honest mapping
for moving a repo across — including what you should *not* move yet.

## Where the two models stand

| model | entrypoint | status |
|---|---|---|
| modules | `env.toml` + `hosts/<name>.ts` selecting `modules/*.ts` | legacy — retained readers and execution, including legacy activation hooks; removed constructors below are not restored |
| workspace | one root `gripsack.ts` | the active development surface |

`grip apply --help` labels the host/module model "legacy". That word
is a direction of travel, not a countdown: **no removal date is set**.
A module repo that does everything you need has no obligation to move.
New capability — coherent Conda/Pixi environments, executing profile
hooks, platform-keyed locks — lands as workspace outputs.

## What maps to what

| in the module repo | in the workspace |
|---|---|
| `hosts/<name>.ts` — one entrypoint per machine, `defineEnv((ctx) => …)` | one root `gripsack.ts`; workspace outputs replace host entrypoint selection |
| per-host parameters (template vars computed from `ctx.facts`) | values computed in the entrypoint; `targetPlatform({ os, arch, abi })` describes command compatibility, not a machine identity |
| per-host binary destinations in module `install` | profile file destinations — `symlinkTo` / `trackedCopyTo` / `managedBlock`; toolchain launchers use the retained environment wrappers |
| `locks/<host>.lock` — one lockfile per host | one `gripsack.lock`, keyed by platform rather than hostname |
| ownership modes `symlink` / `trackedCopy` / `merge` / `template` | `symlinkTo` / `trackedCopyTo` / `managedBlock` / `templateText` — semantics unchanged |
| `pixi(package)` provider | `conda.environment(...)` or `pixi.fromLock(...)` — below |

Config ownership is unchanged between the models: store-owned
symlinks, drift-preserving tracked copies, delimited managed blocks,
rendered templates — the same table as
[ownership modes](modules.md#ownership-modes). The contract is the
same, but changing entrypoint/state roots is a deliberate ownership
cutover, not automatic transfer of another store's history.

## Removed: `pixi(package)`

The old callable `pixi("name", { … })` constructor was removed in
0.44. Calling the public `pixi` binding now reports an E130 migration
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
updates as well. For a cross-host libc/kernel solve baseline, declare
`systemRequirements` in native `conda.environment`, or
`[system-requirements]` in the manifest used for a Pixi import — see
[solve baselines](environments.md#solve-baselines). Neither replaces
actual archive/CPU/runtime admission on the receiving host.

There are two separate decisions: approve the source bytes for
evaluation, then explicitly refresh the imported frozen identity.
For a deliberately reviewed manifest or lock edit:

```sh
set -eu
grip trust inspect --json
# Load this edit's exact reviewed values from your review, not inspect.
: "${reviewed_bundle:?review the changed inputs first}"
: "${reviewed_policy:?review the changed policy first}"
grip trust add --bundle "$reviewed_bundle" --policy "$reviewed_policy"
if result=$(grip check 2>&1); then
  echo "expected a stale frozen-input refusal" >&2
  exit 1
fi
printf '%s\n' "$result"
case "$result" in
  *'Pixi input '*'differs from its frozen identity'*) ;;
  *) echo "unexpected failure — stop and investigate" >&2; exit 1 ;;
esac
grip update
```

Read the failure: the expected refusal is E301, naming the changed
Pixi input and its frozen identity; an unrelated error is not proof.
After `update`, inspect the capture and resulting `gripsack.lock`
again. Use the [unattended comparison](safety.md#unattended-approval)
with newly reviewed expected digests, then `grip check` and apply the
profile. Do not keep using the pre-update approval.

Measured with the promoted 0.45.0 binary on modern Linux and UBI 8:
adding a comment to **each of `pixi.toml` and `pixi.lock` separately**
still failed `check` after the changed source had been approved.
Each explicit `update` followed by review/reapproval made `check`
succeed. The imported 42-archive closure stayed identical: refreshing
the document identity was not a re-solve or an integrity bypass.

## Lockfiles

Legacy resolution pins one `locks/<host>.lock` per host: N machines,
N lockfiles, each resolved on its own host. A workspace writes **one
platform-keyed `gripsack.lock`**: per platform it records immutable
exact archives plus the solve's recorded assumptions. Identity is not
portability — before reusing or re-solving a lock across hosts, read
[solve baselines](environments.md#solve-baselines).

## Running both during migration

Keep **separate entrypoint roots** while migrating: for example, a
`legacy-env/` checkout containing `env.toml`, `hosts/` and `modules/`,
and a sibling `workspace-env/` checkout containing its own `env.toml`
and `gripsack.ts`. Run commands from the appropriate checkout.
Adding a root `gripsack.ts` to the legacy checkout **shadows the
`hosts/*.ts` entrypoints**; `--host` is not a switch back to the module
model or a workspace selector.

Use distinct private `GRIPSACK_HOME` directories and disjoint
destinations while comparing deployments. Separate state roots and
workspace identities do **not** share recorded ownership.
`--take-over` is not an ownership migration command: it does not
transfer a legacy generation's ownership to a workspace.

### Apply the legacy prune before switching

For paths that both configurations would manage, perform two separate
applies. Keep the old checkout, host entrypoint and its original
private state available throughout the cutover:

1. **Stay on the legacy entrypoint.** Do not add `gripsack.ts` yet.
   Remove the shared module declarations from `hosts/<old-host>.ts`
   (or remove just their shared destinations). Preserve unrelated
   modules. Removing declarations alone releases nothing.
2. Review the edited legacy capture and approve its exact bundle and
   policy digests using [unattended approval](safety.md#unattended-approval).
   From the legacy checkout, with the **original** `GRIPSACK_HOME`,
   run `grip plan --host old-host` and review the prune list. Then run
   `grip apply --host old-host` **without a module selector**, so the
   full legacy host commits the prune generation.
3. Confirm that this apply succeeded and the shared paths were
   released. Ordinary tracked-copy drift remains preserved, not
   silently removed: a preserved destination is not a successful
   clean cutover. Stop and resolve it through the normal ownership
   workflow rather than deleting files or editing journals.
4. **Only now switch entrypoints.** Add the root `gripsack.ts`, or
   move to the separate workspace checkout and its deliberately
   chosen private state. Review/approve that source, run `grip update`,
   review the resulting `gripsack.lock` and captured inventory, then
   approve the new exact digests again. Review `grip plan` and apply
   the intended profile, for example `grip apply personal`.

There is a deliberate interval between steps 2 and 4 during which
pruned tools/configuration are **absent**. Schedule the cutover
accordingly; this is not an atomic transfer across identities.
If a prior unmanaged file was retained for restoration, pruning can
restore it instead of leaving an absent path: inspect the result
before the new profile claims it. Do not roll an old legacy
generation back over paths now owned by the workspace.

Positive fixture evidence with public 0.45.0 on Linux/WSL: a legacy
symlink was deployed in generation 1, an independently reviewed
empty legacy host pruned it in generation 2, then a reviewed root
workspace update/reapproval/apply deployed a tracked copy at the same
destination in generation 3. No `--take-over`, manual destination
deletion or state editing was used.

Platform-keyed locking does not mean host-specific configuration
disappears: two machines with the same OS/architecture/ABI share a
platform key, not a hostname or a guarantee of identical runtime
capabilities. Review output selection and the recorded solve baseline
separately.

## Downgrade boundary

**Newer-format state is not generally downgrade-supported.** Keep the
newer binary to operate on it; do not point an old binary at it to
apply, roll back, recover or collect it. Older released binaries were
not retroactively patched.

Limited observations with completed transactions on 2026-10-06:
0.42.0 collected and rolled back a simple legacy generation and a
file-only workspace fixture left by 0.44.1. Those cases do **not**
establish general downgrade safety. With a structured environment
generation, 0.42.0 `gc` refused the unknown `kind` field, while bare
`rollback` returned no readable rollback target (exit 1). That is not
a successful rollback. `status` was not available in 0.42.0.

Workspace-hook generation manifests use the 0.45 version-2 envelope,
which old readers reject. The new binary retains readers for older
formats; that forward-upgrade compatibility is not a promise that an
old binary understands new journals, activation records or generation
manifests. Preserve backups and use the newer binary for recovery.
