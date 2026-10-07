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

Verified end-to-end on 0.44.1 (Ubuntu 24.04 laptop): solve, apply,
activation and re-apply. Not verified: the full tool set across both
review hosts.

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

Personal destinations under `~` are the common case. Absolute shared
destinations (a team-wide `/usr/local/bin`) are your paths at your
privileges — the
[destination boundary](safety.md#the-destination-boundary) applies
unchanged. End-to-end shared-destination deployment on an ephemeral
host is not something we have verified: read `grip plan` before a
first shared apply.
<!-- UNRESOLVED: the external review asked for verified noninteractive
     shared /usr/local/bin integration (initialization and rollback
     included). Only destination-grammar admission is verified here
     (SDK asDestinationPath: absolute or ~/ with normalized segments;
     kinds symlink/tracked_copy/managed_block). Do not claim verified
     shared-destination behavior until it is actually run. -->

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
so the frozen closure is complete, e.g. `packages: { nodejs:
"=26.10.0", "xorg-libx11": "*" }`.

Pyright validation on the glibc 2.28 target remains pending: the
guidance above is the direction, not a verified outcome.

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
