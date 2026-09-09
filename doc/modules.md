# Writing modules

A module is the unit of your environment: how to get a tool, build it,
where its files and configs live. Two authoring styles, same IR.

## Data style (most modules)

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">modules/helix.ts</span></div>
<pre><code class="language-typescript">import { githubRelease, module, symlink, trackedCopy } from "@gripsack/core";

export default module("helix", {
  fetch: githubRelease({
    repo: "helix-editor/helix",
    asset: "helix-{version}-x86_64-linux.tar.xz",
  }),
  install: { "bin/hx": symlink("~/.local/bin/hx") },
  config: { "config.toml": trackedCopy("~/.config/helix/config.toml") },
});</code></pre>
</div>

The core expands the fields into the conventional pipeline:
`fetch → build → install → config → verify → activate`.

## Explicit steps (full control)

When declarative fields cannot say it, a module spec carries `steps`
directly — one fetch per module (the lockfile pins one payload;
E118 refuses more with a hint to split):

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">modules/patched.ts</span></div>
<pre><code class="language-typescript">import { fetchStep, fileFetch, installStep, module, shellStep, symlink } from "@gripsack/core";

export default module("patched", {
  steps: [
    fetchStep(fileFetch("payloads/hello.tar.gz")),
    shellStep("patch -p1 &lt; fix.patch", "patch", { needs: ["fetch"] }),
    { ...installStep({ "bin/hx": symlink("~/.local/bin/hx") }),
      needs: ["patch"] },
  ],
});</code></pre>
</div>

Explicit steps do not mix with declarative
`fetch`/`build`/`install`/`config`/`activate` fields. Source staging,
config lint and module-level verification work in either style.
Write `needs` explicitly; declaration order breaks ties between ready
steps but is not an implicit dependency.

There was a class style (`class X extends Module`); it was removed in
0.18.0 — **prefer a factory function** for reuse, which keeps
modules values:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">modules/lang-servers.ts</span></div>
<pre><code class="language-typescript">import { githubRelease, module, symlink } from "@gripsack/core";

export function langServer(name: string, repo: string) {
  return module(name, {
    fetch: githubRelease({ repo, asset: `${name}-{version}.tar.gz` }),
    install: { [`bin/${name}`]: symlink(`~/.local/bin/${name}`) },
  });
}

export const lua = langServer("lua-ls", "LuaLS/lua-language-server");
export const zed = langServer("zed", "zed-industries/zed");</code></pre>
</div>

## Ownership modes

| mode | behavior | use for |
|---|---|---|
| `symlink(to)` | store-owned, read-only | disciplined tools |
| `trackedCopy(to)` | copied; drift detected, never silently overwritten | apps that rewrite their configs |
| `merge(to, marker?)` | managed block in a shared file | `.bashrc`, `settings.json` other tools also write |
| `template(to, vars?)` | rendered per machine at deploy time | hostnames, work vs personal email |

`merge(to, marker?)` owns exactly one delimited block inside a
file other tools also write — everything outside the markers is never
touched. Content drift *inside* the markers self-heals on apply; prune removes
only an intact block. The open marker records its content hash and the hosting
file's permission mode (`sha=<16hex> mode=0644`). Chmod-only drift is preserved
and warned, not silently accepted as intact or deleted during prune.
Older markers acquire mode metadata on the next deployment.
One lossless inspection feeds both reporting and rewriting. Complete duplicates
are reconciled and edits in any duplicate are reported, but conflicting mode
evidence blocks mutation regardless of order. Unmatched, nested or interleaved
markers fail before mutation: text following an unmatched opener is not silently
claimed as managed content. Foreign bytes, including trailing whitespace, remain
outside the replacement ranges.
Sharing one physical destination between modules is rejected. The comment style
is inferred from the destination (`.jsonc` → `//`, `.vimrc` → `"`,
`.html` → `<!-- -->`, rc files and everything unknown → `#`);
`marker` overrides the prefix.

`template(to, vars?)` substitutes `{{ name }}` placeholders in
the payload at deploy time; `{{{{` renders a literal `{{` (payloads
that themselves carry template syntax — helm values, jinja configs —
are expressible). An undefined variable fails the apply loudly, never
renders empty. Compute per-host values in the host entrypoint from
`ctx.facts` — the core stays a dumb substituter.

Fresh tracked copies and templates land at 0755 for an executable payload,
otherwise 0644. Takeover retains the destination's full permissions. Later
content updates preserve acquired access bits; source executable-bit changes
update executability without granting new read/write access.

Templates are whole-file outputs: their manifest records SHA-256 identity over
the **rendered bytes and full permission mode**. No banner is injected into
configs or scripts. Chmod is drift just like a content edit: visible in plan,
preserved with a warning on apply/rollback, and guarded against prune even
after repeated apply. Authorized rollback restores the recorded mode exactly.
Old template receipts remain readable; both their bytes hash and separately
recorded mode must match before they authorize a change.

Merge preserves an existing host's mode; a newly created host uses 0644.
`store-verify` reports active template/merge chmod drift separately from store
corruption—`--repair` does not delete healthy artifacts because outputs drifted.

Payload keys and payload `verify` paths can use `{version}` for the raw locked
tag or `{version.bare}` to remove one leading lowercase `v`. Asset matching's
legacy fallback does not silently change path spelling. See
[fetch placeholders and preflight](fetchers.md#placeholders).

## Steps, resources and execution contracts

Explicit steps carry `needs` (sibling ids or `module:step`), `resources`
(named mutexes — declare them first with `resource("pixi.lock")`; a
typo fails at eval), and `verify` contracts. The action ladder:
typed primitives → `runStep` (argv as data) → `shellStep` →
`gripfetch-*` plugins for transports.

Cross-module `needs` waits for the producer module's pre-activation work,
including verification. This is module-granular ordering, not a global
step scheduler. It does not deploy a build-only module or provide PATH
exports: use dependency purposes for those. `producer:done` names its
pre-activation barrier. Activation targets, self-qualified references and
cycles in the combined ordering graph fail before mutation.

Build, custom-shell and structured run steps are **cached artifact
recipes**. Declared outputs must exist after shell and run actions;
omitting outputs does not make a step run on every apply. Effects that
belong at activation go in `customHook`. The inert module/step `retries`
field was removed in 0.36.0 rather than pretending arbitrary effects
have a safe automatic retry policy.

## Conditionals (hosts, facts, tags)

Gating lives in the host entrypoint, not in module specs:
`hosts/<name>.ts` default-exports a `defineEnv` function that receives
`ctx` — the machine's facts (os, arch, libc, hostname), your CLI
tags, declared probes — and returns the environment. Falsy module
entries drop out, so a gate is just `&&`:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">hosts/laptop.ts</span></div>
<pre><code class="language-typescript">import { defineEnv } from "@gripsack/core";
import steam from "../modules/steam.ts";
import cuda from "../modules/cuda.ts";

export default defineEnv((ctx) => ({
  tags: ["gui"],
  modules: [
    ctx.facts.os === "linux" && steam,
    ctx.probe.executable("nvidia-smi") && cuda,
  ],
}));</code></pre>
</div>

`when({ os: "linux", tags: ["gui"] }, ctx)` and `hasTag("cli", ctx)`
are the structured spellings over the same `ctx`. The facts arrive
core-injected — eval is sandboxed and observes nothing about the
machine on its own — and `ctx.probe.*` is a symbolic request the core
binds (a PATH lookup, a file stat) in a second eval pass; probes
re-evaluate every run and `grip plan` summarizes them under a
host-inputs header.

Per-file conditionals are plain code where `ctx` is in scope — the
host entrypoint again, different source, same destination:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">hosts/laptop.ts — per-file conditionals</span></div>
<pre><code class="language-typescript">import { defineEnv, hasTag, module, trackedCopy } from "@gripsack/core";

export default defineEnv((ctx) => ({
  modules: [
    module("zed", {
      config: {
        [hasTag("spaces", ctx) ? "settings.spaces.json" : "settings.laptop.json"]:
          trackedCopy("~/.config/zed/settings.json"),
      },
    }),
  ],
}));</code></pre>
</div>

Facts stay curated on purpose: os/arch/libc/hostname plus tags.
Anything beyond that is a probe (`ctx.probe.executable`,
`ctx.probe.file_exists`) or plain code in the host entrypoint — the
entrypoint *is* the extension point.

## Dependencies

`dep("git")` is a runtime dependency. Since **core and TypeScript 0.35.0**,
`dep("compiler", { for: "build" })` prepares a build closure instead:

```ts
import { dep, installStep, module, shellStep, symlink } from "@gripsack/core";

export default module("consumer", {
  depends: [dep("compiler", { for: "build" })],
  steps: [
    shellStep('mkdir -p out && cp "$(command -v cc)" out/built', "build"),
    installStep({ "out/built": symlink("~/.local/bin/built") }, "install", {
      needs: ["build"],
    }),
  ],
});
```

Both modules must be listed in the host environment. The compiler must
publish an executable at `bin/cc`. A module with incoming build edges
and **no incoming runtime edge** is build-only: no destination links or
copies, activation hooks, or shell-profile exports. Any incoming runtime
edge wins; a standalone module deploys normally. Subset applies use the
same whole-graph rule. Remove both declarations when retiring the
consumer and its tool; leaving the tool standalone means you want it
deployed.

Build, custom-shell, and structured `runStep` processes get:

- dependency `bin/` directories **prepended** to PATH in dependency-first
  graph order, retaining an explicit step PATH or the ambient PATH;
- `GRIP_DEP_COMPILER` pointing to the compiler's store root. Names are
  uppercased, with punctuation mapped to `_`; ambiguous aliases in one
  closure are rejected with E123 rather than overwritten.

The closure follows build edges transitively and deduplicates diamonds.
A build tool's runtime dependencies are **not** in that closure: they
deploy through runtime edges. This is not a hermetic build sandbox;
ambient tools remain available, and arbitrary shell steps still run
with your privileges. Module `env` exports do not flow into dependents.

Payload verification runs normally and retains receipts tied to the
store identity. Destination checks are omitted for build-only modules.
The manifest keeps store-only module records (no deployment effects)
and the consumer's `build_closure`. **Every retained generation** pins
its paths; GC collects them after those generations are pruned.
Rollback restores the recorded consumer files and never rebuilds.

### IR v3 migration

0.36.0 emits and accepts **IR v3** only. Remove module/step `retries`;
untyped declarations fail explicitly rather than ignoring the field.
Update a pinned frontend with
`npm install --save-dev @gripsack/core@^0.36.0`, or remove the pin to use
the embedded copy. v1/v2 input fails with E100 before field decoding.
Existing lockfiles and generations remain readable.

Dependency purposes still use `for`, not the v1 `edge` field.
`dep("rust", "build")` becomes `dep("rust", { for: "build" })`;
unknown purposes receive source-labeled E122 diagnostics.

## npm dependencies in module code

Module code is TypeScript — it can import npm packages from the env
repo's own `package.json` + `node_modules` (BYONM). gripsack does not
fetch or manage them: you install them, they're evaluated read-only,
and they run under the exact same sandbox as your module code — no
env, no network, no subprocesses, no filesystem outside the repo. A
dependency that needs an effect fails loudly at eval; that effect
belongs in a probe or a fetcher, not in a library.

The repo's `package.json` is one IDE story: `@gripsack/core` as a
devDependency gives editors autocomplete and inline errors on module
code, and doubles as the deliberate pin (0013 D3 — the repo's install
shadows the embedded frontend). `grip init` scaffolds all of it:
`package.json` pinned to a compatible version, `tsconfig.json`,
`.gitignore`, and a fresh `git init`.

Since 0.40 there is a registry-free path too: the frontend the binary
embeds materializes at `$GRIPSACK_HOME/frontend/ts-<version>/` with a
stable `frontend/current` symlink, and its `package.json` resolves
types straight from `src/`. Point your editor at it — symlink
`node_modules/@gripsack/core` to `$GRIPSACK_HOME/frontend/current`, or
add a tsconfig `paths` entry for `@gripsack/core` →
`$GRIPSACK_HOME/frontend/current/src/index.ts` — with
`npm i -D @types/node` and `noEmit` + `allowImportingTsExtensions` in
your tsconfig. `grip doctor` prints the exact wiring for your machine.
