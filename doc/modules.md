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

## Class style (full control)

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">class style — full control</span></div>
<pre><code class="language-typescript">import {
  Module, define, fetchStep, fileFetch, installStep, shellStep, symlink,
} from "@gripsack/core";

class Patched extends Module {
  fetch() {
    return fetchStep(fileFetch("payloads/hello.tar.gz"));
  }
  build() {
    return shellStep("patch -p1 &lt; fix.patch", "patch");
  }
  install() {
    return installStep({ "bin/hx": symlink("~/.local/bin/hx") });
  }
}

export default define(Patched);</code></pre>
</div>

Phase methods return a step or a list of steps; the pipeline chains
them in order — within a phase and across boundaries — so you write
`needs` only for cross-cutting edges. **Phase methods run at eval time
only**: they build data, they never run at build time.

## Ownership modes

| mode | behavior | use for |
|---|---|---|
| `symlink(to)` | store-owned, read-only | disciplined tools |
| `trackedCopy(to)` | copied; drift detected, never silently overwritten | apps that rewrite their configs |
| `merge(to, marker?)` | managed block in a shared file | `.bashrc`, `settings.json` other tools also write |
| `template(to, vars?)` | rendered per machine at deploy time | hostnames, work vs personal email |

`merge(to, marker?)` owns exactly one delimited block inside a
file other tools also write — everything outside the markers is never
touched. The block is regenerated wholesale on every apply (drift
*inside* the markers self-heals), prune removes only the block, and
two modules can each own a block in the same file. The comment style
is inferred from the destination (`.jsonc` → `//`, `.vimrc` → `"`,
`.html` → `<!-- -->`, rc files and everything unknown → `#`);
`marker` overrides the prefix.

`template(to, vars?)` substitutes `{{ name }}` placeholders in
the payload at deploy time; `{{{{` renders a literal `{{` (payloads
that themselves carry template syntax — helm values, jinja configs —
are expressible). An undefined variable fails the apply loudly, never
renders empty. Compute per-host values in the host entrypoint from
`ctx.facts` — the core stays a dumb substituter.

## Steps, resources, retries

Explicit steps carry `needs` (sibling ids or `module:step`), `resources`
(named mutexes — declare them first with `resource("pixi.lock")`; a
typo fails at eval), `verify` contracts, and `retries` overrides. The
action ladder: typed primitives → `runStep` (argv as data) →
`shellStep` (last rung) → `gripfetch-*` plugins for transports.

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

`dep("git")` is a runtime edge; `dep("rust", "build")` is an
ephemeral build-only dependency — present while building, GC'd after.
