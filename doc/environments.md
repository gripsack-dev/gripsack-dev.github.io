# Persistent environments

A workspace `profile` can deploy a solved toolchain — coherent Conda
or Pixi packages, command wrappers, config files — through the same
generation/rollback transaction module repos use, and expose it to any
shell through one plain file.

## A profile with a real toolchain

The complete, verified shape — node 26.10.0 solved from conda-forge,
exposed as a `node` command:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts</span></div>
<pre><code class="language-typescript">import {
  defineWorkspace, environment, pkg, profile, provider, conda,
  targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });
const node = pkg("node", {
  producer: provider(conda.environment({
    channels: ["conda-forge"],
    packages: { nodejs: "=26.10.0" },
  })),
  commands: { node: "bin/node" },
  target,
  layout: { kind: "prefix_materialized" },
});
const tools = environment("tools", { packages: ["node"], target });

export default defineWorkspace(() => workspace({
  outputs: [node, tools, profile("with-node", { environment: "tools" })],
}));</code></pre>
</div>

The pieces: `conda.environment` solves one coherent environment (a
frozen Pixi lock works the same way through
[pixi.fromLock](workspace-migration.md#removed-pixipackage)); `pkg`
turns it into named commands over a materialized prefix;
`environment` is a process-scoped selection of packages — it deploys
no personal profile by itself; `profile` ties the environment (plus
optional config files) into the generation transaction.

The promoted 0.45.0 Linux binary was also exercised with real Node
26.10.0 and pyright 1.1.414: personal-bin activation on glibc 2.39,
and `/usr/local/bin` activation inside disposable UBI 8 userspace
(glibc 2.28), including a second generation and actual rollback.
Both used the same reviewed frozen Pixi closure described below.

## Activation: profile.sh

`grip apply` generates `$GRIPSACK_HOME/current/env/profile.sh`
(default `$GRIPSACK_HOME`: `~/.local/share/gripsack`). Source it from
any POSIX shell:

```sh
. "$GRIPSACK_HOME/current/env/profile.sh"
command -v node && node --version   # the wrapper is on PATH — 26.10.0
```

The contract is deliberately boring:

- **plain `/bin/sh`** — no shell-specific features required. Verified
  sourcing with cwd `/` and an initial `PATH=/usr/bin:/bin`.
- **wrappers on `PATH`** — each declared command is exposed after
  sourcing (`node --version` prints `26.10.0`).
- **second apply is satisfied** — a repeat `grip apply` reports
  already satisfied without re-solving.

gripsack does not edit shell startup files automatically. A login-shell
profile may source this file explicitly; noninteractive `/bin/sh` does
not read `~/.profile`, so use an explicit source command or the launcher
below. `grip run --env tools …` and `grip shell tools` are process-scoped
alternatives, not changes to an already running parent shell.

Apply and rollback change `current`, not the environment of existing
processes. Use a fresh shell/environment afterward. Re-sourcing prepends
the selected paths and sets declared variables; it does not remove old
PATH entries or unset variables omitted by the restored generation.
The launchers below source the current selection afresh on every call.

## Destinations: personal and shared

Profile files declare destinations with the same ownership semantics
as module configs: `symlinkTo(path)` (store-owned, read-only),
`trackedCopyTo(path)` (copied, drift detected), `managedBlock(path,
marker)` (one delimited block in a shared file). A destination path is
**absolute or `~/`-prefixed, with normalized segments** —
`~/.local/bin/my-tool` and `/usr/local/bin/my-tool` are both admitted,
and the rule is enforced at authoring time, mirroring the core's
runtime admission, so an escaping path fails in your editor rather
than mid-apply.

These are **file destination rules**, not permission to project files
from an arbitrary Conda prefix. For a persistent toolchain, use the
generated `current/env/profile.sh`: it selects the retained
generation's command wrappers. Do not hard-code a store hash or
symlink directly to the prefix's `bin/node`.

### Initialize and approve

For a new personal workspace, run as the UID that will run the tools:

```sh
set -eu
umask 077
export GRIPSACK_HOME="$HOME/.local/share/gripsack"
mkdir -p "$GRIPSACK_HOME"
grip init "$HOME/node-workspace"
cd "$HOME/node-workspace"
```

Save the complete `gripsack.ts` above at this root. It supersedes the
generated legacy host entrypoint; you do not need a host shim. Before
the first solve, inspect and review the capture, then use the exact
values from that review (not an automatic assignment from `inspect`):

```sh
grip trust inspect --json
# After review, load reviewed_bundle and reviewed_policy out-of-band.
: "${reviewed_bundle:?review the initial source first}"
: "${reviewed_policy:?review the initial policy first}"
grip trust add --bundle "$reviewed_bundle" --policy "$reviewed_policy"
grip update
```

The lock write changes the captured bundle. Review the resulting
`gripsack.lock` and inventory, then use the
[expected-digest comparison](safety.md#unattended-approval) with the
**new** reviewed values before `grip apply with-node`. On a machine
receiving an already frozen, reviewed checkout, skip `grip update`:
compare, approve and apply without re-solving.

### Personal command

After `grip apply with-node`, install a small launcher outside the
checkout. The distinct name avoids overwriting an unrelated `node`.
This launcher is an operator-installed front door, not a
gripsack-managed profile file; rollback changes its selected
environment, not the launcher itself.

```sh
set -eu
launcher="$HOME/.local/bin/gripsack-node"
mkdir -p "$HOME/.local/bin"
test ! -e "$launcher"
test ! -L "$launcher"
printf '#!/bin/sh\nset -eu\n. "%s/current/env/profile.sh"\nexec node "$@"\n' \
  "$GRIPSACK_HOME" > "$launcher"
chmod 755 "$launcher"
env -i PATH=/usr/bin:/bin /bin/sh -c 'cd / && "$1" --version' sh "$launcher"
```

The pre-existing-destination checks stop installation rather than
overwrite another tool. The absolute state path embedded in the
launcher must remain stable. It works without a login shell, a
working-directory assumption or an inherited `HOME`.

### Noninteractive service command

For `/usr/local/bin/gripsack-node`, do this **inside a disposable
container** to try it, not in the host's system directories. Use one
deployment/runtime UID with permission to create the launcher. The
measured UBI 8 case used UID 0 for both, a private mode-0700
`GRIPSACK_HOME`, and no user HOME or credentials mounted into it.
In production, choose and provision the service's paths deliberately.

Use the same initialization/approval/apply sequence under that UID,
with its private state outside the checkout, then replace the
personal installation block with:

```sh
set -eu
launcher=/usr/local/bin/gripsack-node
test ! -e "$launcher"
test ! -L "$launcher"
printf '#!/bin/sh\nset -eu\n. "%s/current/env/profile.sh"\nexec node "$@"\n' \
  "$GRIPSACK_HOME" > "$launcher"
chmod 755 "$launcher"
env -i PATH=/usr/bin:/bin /bin/sh -c \
  'cd / && /usr/local/bin/gripsack-node --version'
```

An absolute launcher location does **not** provide multi-user access
to a private store. Do not widen permissions on `GRIPSACK_HOME`.
The [destination boundary](safety.md#the-destination-boundary) still
applies to profile-managed files.

### Rollback through the same launcher

To make a second generation observable, import `lit` in the complete
workspace above and add `env: { MIGRATION_REVISION: lit("second") }`
to `environment("tools", …)`. Review/approve the changed source, run
`grip update`, review any changed lock and approve its exact capture,
then:

```sh
grip apply with-node
env -i PATH=/usr/bin:/bin /bin/sh -c \
  'cd / && "$1" -p "process.env.MIGRATION_REVISION || '\''initial'\''"' sh "$launcher"
grip rollback
env -i PATH=/usr/bin:/bin /bin/sh -c \
  'cd / && "$1" -p "process.env.MIGRATION_REVISION || '\''initial'\''"' sh "$launcher"
```

The two invocations print `second`, then `initial`; `--version`
continues to print `v26.10.0`. This was observed through both the
personal and container system launcher with plain `/bin/sh`, cwd
`/`, initial `PATH=/usr/bin:/bin`, and no inherited shell activation.
The retained environment wrappers and prior generation remain the
authority; the launcher is unchanged.

## Complete closures

A frozen prefix must carry its whole runtime — that is the point.
pyright 1.1.414 with an explicit glibc 2.28 target failed activation
exactly as intended:

```text
Conda prefix requires "libX11.so.6" outside the explicit OS runtime; include that library in the frozen package closure
```

That is fail-closed missing-library detection working, not a pyright
verdict. The fix is to declare the missing runtime library as an
explicit package — for libX11 the conda-forge `xorg-libx11` family —
so the frozen closure is complete. The exercised Pixi manifest used:

```toml
[workspace]
name = "gripsack-pixi-gate"
channels = ["conda-forge"]
platforms = ["linux-64"]

[system-requirements]
libc = { family = "glibc", version = "2.28" }

[dependencies]
pyright = "*"
"xorg-libx11" = "*"
```

The reviewed Pixi v7 lock, not the wildcard, fixes the deployed
versions: it selected nodejs 26.10.0, pyright 1.1.414, xorg-libx11
1.8.13 and the transitive X11 libraries. It was imported with
`pixi.fromLock`, explicit `abi: "gnu"`, commands `node: "bin/node"`
and `pyright: "bin/pyright"`, a materialized-prefix package, an
environment selecting it, and a profile selecting that environment.

On 2026-10-08 the **same 42 exact archives** ran real `node --version`
and `pyright --version` on modern Linux (glibc 2.39) and in UBI 8
userspace (glibc 2.28). The UBI run had networking disabled and reused
the verified archive cache, not an updater's fresh solve. It recorded
`__glibc=2.28` and `__linux=4.18` in the frozen assumptions. Both
runtimes shared the available WSL2 6.18 kernel: this is not testing
the external reviewer's el9 5.14 kernel or private repository, and
does not qualify all possible packages.

## Solve baselines

Where a solve grounds, and what a lock does and does not prove:

- **Native `conda.environment` solves are host-relative.** They ground
  in the *updater's* measured libc/kernel virtual packages. An
  explicit target `abi: "gnu"` admits GNU commands for that platform;
  it is **not** a portability baseline.
- **The platform-keyed `gripsack.lock` records identity.** Per
  platform it stores immutable exact archives plus the solve's
  recorded assumptions (`system_requirements`, `virtual_packages`) —
  evidence of what was solved, not proof the result runs elsewhere.
- **The explicit baseline path** declares the floor in the imported
  Pixi manifest and freezes with `pixi.fromLock`:

  ```toml
  [system-requirements]
  libc = { family = "glibc", version = "2.28" }
  ```

  The solve respects the declared baseline and records exact
  archives. Three things remain yours to verify, separately: (1) the
  solve respected the baseline during `grip update`; (2) the selected
  archives meet each host's actual CPU/libc; (3) sealed-loader
  admission is independent — the bound platform loader is probed for
  its controls (RHEL 8's backporting glibc 2.28 qualifies; a loader
  missing any control fails closed, naming it).
- **A lock without an explicit baseline carries host-relative
  assumptions.** Make a deliberate baseline decision before
  cross-host reuse or re-solving.

## Hooks and checks

Since 0.45.0, profile hooks execute for real — no more
passes-`check`-fails-`apply` gaps:

| capability | status in 0.45.0 | notes |
|---|---|---|
| profile hooks `post_link`, `post_activate`, `on_remove` | **execute**, through the durable activation ledger | per-intent identity, durable terminal outcomes, ambiguous-crash replay handling, **no automatic rollback** after a post-activation failure |
| hook commands | literal `exec`, explicit `packageCommand`/`runBash`, artifact/input arguments, declared `env` and `cwd` | hooks do **not** implicitly source the newly activated `profile.sh`; default cwd follows the legacy hook temp-directory convention |
| task `checks` | ordered postconditions after successful task steps | once per invocation, stopping at the first failure; `sourcePath` resolves against the immutable check subject |
| recipe publication checks | unchanged | as before |

Still explicitly unavailable — each refused with a diagnostic, never a
silent no-op: profile `file.checks` stage adapters, schedules
(registration), task prerequisites.

`grip check` and `grip plan` stay read-only: "running a check" means
recipe publication validation or task postconditions, never side
effects from a preview.

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts — a profile hook</span></div>
<pre><code class="language-typescript">import { exec, hook, lit } from "@gripsack/core";

// selected with profile(…, { hooks: ["after"] }) — executes on apply
export const after = hook("after", {
  trigger: "post_link",
  run: exec({ argv: [lit("/usr/bin/true")] }),
});</code></pre>
</div>

On the wire, activation plans, pending pointers and outcome records
advanced to version 2 (version 1 remains readable; legacy actions keep
byte-identical serialization). Generation manifests carrying workspace
hooks use an explicit `{version: 2, …}` envelope that older binaries
reject before any effects; ordinary manifests keep the historical
shape. The downgrade boundary is measured and documented in
[workspace migration](workspace-migration.md#downgrade-boundary).
