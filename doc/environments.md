# Persistent environments

A workspace `profile` can deploy a solved toolchain — coherent Conda
or Pixi packages, command wrappers, config files — through the same
generation/rollback transaction module repos use, and expose it to any
shell through one plain file.

## A profile with a real toolchain

This complete declaration targets core/SDK 0.46: node 26.10.0 from
conda-forge, with an explicit Linux/glibc solve baseline and a `node` command.

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
    systemRequirements: {
      libc: { family: "glibc", version: "2.28" },
      linux: "4.18",
    },
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

For package closures explicitly using
[`hostRuntime`](safety.md#explicit-host-runtime-dependence), generated
wrappers additionally depend on the absolute installed core executable
and original private state path. Keep both stable: the managed runner
revalidates the retained closure and host libraries at each launch,
rather than bypassing admission through a raw loader command.

If the core moves, invoke it at its new absolute path and reapply the profile,
then start a fresh shell or source the refreshed activation file. An old
wrapper deliberately does not search `PATH` for a replacement core. This
recovery was exercised with a retained host-dependent profile on glibc 2.28;
moving the private state itself is not covered by that recovery recipe.

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

### Profile-managed personal command

A launcher is already expressible as an ordinary profile file; no
dedicated launcher helper is required. Its **source file's executable
bit** supplies executability. `file(...)` has no `mode` option, and
origin-free `literalText(...)` does not supply an executable bit.

From the initialized workspace, create this reviewed repository
source **before** source approval:

```sh
set -eu
: "${GRIPSACK_HOME:?initialize the private state path first}"
mkdir -p launchers
test ! -e launchers/gripsack-node
test ! -L launchers/gripsack-node
printf '#!/bin/sh\nset -eu\n. "%s/current/env/profile.sh"\nexec node "$@"\n' \
  "$GRIPSACK_HOME" > launchers/gripsack-node
chmod 755 launchers/gripsack-node
```

Review the generated shell text and retain its executable bit in
version control. The example initialization uses an absolute state
path; keep that path stable. The launcher does not need an inherited
`HOME`, a login shell or a particular working directory.

This complete workspace replaces the first card and adds the managed
launcher to the same profile:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts — managed launcher</span></div>
<pre><code class="language-typescript">import {
  conda, defineWorkspace, environment, file, identity, pkg, profile,
  provider, repoFile, symlinkTo, targetPlatform, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64", abi: "gnu" });
const node = pkg("node", {
  producer: provider(conda.environment({
    channels: ["conda-forge"],
    packages: { nodejs: "=26.10.0" },
    systemRequirements: {
      libc: { family: "glibc", version: "2.28" },
      linux: "4.18",
    },
  })),
  commands: { node: "bin/node" },
  target,
  layout: { kind: "prefix_materialized" },
});
const tools = environment("tools", { packages: ["node"], target });

export default defineWorkspace(() => workspace({
  outputs: [node, tools, profile("with-node", {
    environment: "tools",
    files: [file({
      source: repoFile("launchers/gripsack-node"),
      content: identity(),
      destination: symlinkTo("~/.local/bin/gripsack-node"),
    })],
  })],
}));</code></pre>
</div>

Use the review/approve/update/review/reapprove sequence above, then:

```sh
grip apply with-node
launcher="$HOME/.local/bin/gripsack-node"
env -i PATH=/usr/bin:/bin /bin/sh -c 'cd / && "$1" --version' sh "$launcher"
```

The distinct command name avoids claiming an unrelated `node`;
ordinary destination ownership checks still apply. The launcher
bytes, executable intent and destination now participate in the
profile transaction, including prune and rollback. Its source of
runtime selection remains `current/env/profile.sh`, not a copied
Conda executable or a hard-coded store hash.

### Noninteractive service command

For `/usr/local/bin/gripsack-node`, change only the file destination
to `symlinkTo("/usr/local/bin/gripsack-node")` and use the same
review/approval/apply sequence. Try system destinations **inside a
disposable container**, not in the host's system directories.
Initialize and deploy as the runtime UID, with a private mode-0700
`GRIPSACK_HOME` outside the checkout and permission to create the
destination. Provision these paths deliberately before unattended
approval; noninteractive shells do not initialize them for you.

An absolute launcher location does **not** provide multi-user access
to a private store. Do not widen permissions on `GRIPSACK_HOME`.
The [destination boundary](safety.md#the-destination-boundary) still
applies. Earlier UBI 8 evidence used a manually installed launcher
under UID 0; the newly exercised profile-managed launcher was a
personal destination on Linux/WSL, not a new multi-user qualification.

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
continues to print `v26.10.0`. The profile-managed launcher was
exercised with public 0.45.0 and the already reviewed frozen Pixi
Node/pyright closure below, reusing its verified archives without
re-solving. It ran from `/` with only `PATH=/usr/bin:/bin`, no `HOME`
and no inherited activation. The second apply and actual rollback
changed the selected environment through the same managed launcher.
This proves the launcher mechanism, not every future Conda solve.

## Release trees that locate their siblings

`artifactTree(...)` expands into **individually owned files**.
With `symlinkTo(...)`, each destination links to its own retained
content object; it is not one symlink to a directory tree. A program
which resolves its executable's physical path (for example with
`realpath` or `/proc/self/exe`) can therefore lose its expected
`../lib`, `../share` or adjacent-resource relationship even though
the destination directory looks correct.

For release trees that require this physical relationship, deploy
the required tree with `trackedCopyTo(...)`. Each selected regular
file then physically occupies its declared relative location. Include
the runtime data/libraries as well as the executable; copied files
remain individually owned and drift-protected, not an exclusively
owned directory.

This complete local example demonstrates the supported layout
without downloading an unreviewed release. In a fresh workspace,
create these captured source files:

```sh
set -eu
mkdir -p release/bin release/lib
cat > release/bin/sibling-tool <<'SH'
#!/bin/sh
set -eu
self=$(readlink -f "$0")
base=$(dirname "$self")
cat "$base/../lib/message"
SH
chmod 755 release/bin/sibling-tool
printf 'physical-siblings-ok\n' > release/lib/message
```

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gripsack.ts — physical release layout</span></div>
<pre><code class="language-typescript">import {
  artifactTree, defineWorkspace, file, fileFetch, identity, pkg,
  profile, provider, targetPlatform, trackedCopyTo, workspace,
} from "@gripsack/core";

const release = pkg("release", {
  producer: provider(fileFetch("release")),
  commands: {},
  target: targetPlatform({ os: "linux", arch: "x86_64" }),
  layout: { kind: "relocatable" },
});
export default defineWorkspace(() => workspace({
  outputs: [release, profile("release-files", { files: [file({
    source: artifactTree("release", { include: ["bin", "lib"] }),
    content: identity(),
    destination: trackedCopyTo("~/.local/lib/sibling-release"),
  })] })],
}));</code></pre>
</div>

Review/approve the source, `grip update`, review/reapprove the
resulting capture, then `grip apply release-files`. Invoke
`"$HOME/.local/lib/sibling-release/bin/sibling-tool"` from `/`:
it prints `physical-siblings-ok`. This positive workflow was
exercised with public 0.45.0 on Linux/WSL; both selected destinations
were regular files, and the executable bit was retained.

For a real `githubRelease` producer, review the archive's actual
layout and select its required files instead. Selectors retain paths:
selecting `bin` deploys `bin/sibling-tool`, not a flattened filename.
This is **not** arbitrary projection out of a Conda prefix, a
relocation engine for fixed-prefix software, or a promise that any
release can run as a sealed package command. Here `commands: {}`
exports no such command; execution is of the deployed profile file.
Untracked files in the destination directory are not pruned.

## MatchSpec version constraints

`conda.environment({ packages: ... })` maps each package name to a
**MatchSpec version constraint**, not a bare version string. The
native helper parses the package name plus that constraint with
Rattler's strict MatchSpec parser:

| value | meaning |
|---|---|
| `"==25.07.1"` | exact version |
| `"=25.07"` | version-prefix match (the 25.07 series), not exact equality |
| `">=25.07.1,<26"` | intersection of lower and upper version bounds |
| `"*"` | any version at solve time |

Do not write `"25.07.1"`: a bare version is rejected. Put the package
name only in the object key, for example `packages: { nodejs: "==26.10.0" }`.
Use `==` when exact equality is intended; `=26.10.0` in the older
examples is a prefix constraint. The resulting lock records exact
archives even when the declaration uses a range or wildcard; changing
the constraint requires an explicit reviewed update.

## Complete closures

A frozen prefix must carry its whole runtime — that is the point.
pyright 1.1.414 with an explicit glibc 2.28 target failed activation
exactly as intended:

```text
Conda prefix requires "libX11.so.6" outside the explicit OS runtime; include that library in the frozen package closure
```

That is intentional, default fail-closed missing-library detection,
not a new pyright bug or permission to use arbitrary host libraries.
Declare the missing runtime library explicitly — for libX11 the
conda-forge `xorg-libx11` package — so it and its dependencies enter
the reviewed frozen closure. Native declarations use, for example,
`packages: { pyright: "*", "xorg-libx11": "*" }`. The exercised Pixi
manifest used:

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

Native `conda.environment` accepts `systemRequirements` alongside
`channels` and `packages`. For example, add
`systemRequirements: { libc: { family: "glibc", version: "2.28" }, linux: "4.18" }`
to the source declaration to solve for that Linux baseline.
`linux` and `libc.version` are dotted-decimal version strings; the
supported family is exactly `"glibc"`. Unsupported keys/families
and null values diagnose rather than silently using the host.

- **Declared capabilities replace the corresponding measured solve
  virtuals.** Omitted libc/kernel requirements still use the
  updater's measured values. With neither field present, the native
  solve remains host-relative. `target: ... abi: "gnu"` declares
  command ABI compatibility; it is **not** a libc/kernel baseline.
- **The baseline is part of the frozen source contract.** Changing
  it requires `grip update`, review of the resulting lock and renewed
  exact-capture approval. A frozen consumer does not silently solve
  against the new value.
- **The platform-keyed `gripsack.lock` records identity.** It retains
  exact archives and the recorded `system_requirements` and
  `virtual_packages`. A measured updater value such as
  `__glibc=2.39` is not, by itself, every archive's minimum runtime
  glibc. Do not confuse solve provenance with an archive requirement.
- **Pixi imports retain their manifest baseline.** Declare it in
  the manifest before external lock generation, then import the
  reviewed manifest and lock with `pixi.fromLock`:

```toml
[system-requirements]
libc = { family = "glibc", version = "2.28" }
linux = "4.18"
```

A baseline is not universal portability proof. The selected
archives' actual dependencies/constraints, CPU requirements, explicit
system requirements and sealed-loader admission remain independent
runtime checks. The bound GNU loader is probed for its required
controls; a loader missing a control fails closed, naming it.
Make a deliberate baseline decision before cross-host reuse or
re-solving, and qualify the actual resulting closure on those hosts.

The external reviewer reports successful prior profile/Pixi/loader
and hook workflows on WSL Ubuntu 24.04 (glibc 2.39) and RHEL 8.10
(glibc 2.28, el9 5.14 kernel, Landlock). That is **external reviewer
evidence**, not our own private-host qualification. The local
public-0.45.0 smoke results above exercise existing APIs; they do not
claim to exercise the new native `systemRequirements` field.

## Hooks and checks

Since 0.45.0, profile hooks execute on supported runtimes instead of
unconditionally refusing with the unavailable-A2-capability error:

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
