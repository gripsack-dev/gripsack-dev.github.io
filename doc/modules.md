# Writing modules

A module is the unit of your environment: how to get a tool, build it,
where its files and configs live. Two authoring styles, same IR.

## Data style (most modules)

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">helix — python ships today</span>
    <span class="tab-bar">
      <button data-tab="py" class="active" aria-current="true">python</button><button data-tab="ts">typescript</button>
    </span>
  </div>
  <div class="tab-pane" data-pane="py">
<pre><code class="language-python">from gripsack import module, github_release, symlink, tracked_copy
module(
    "helix",
    fetch=github_release(
        repo="helix-editor/helix",
        asset="helix-{version}-x86_64-linux.tar.xz",
    ),
    install={"bin/hx": symlink("~/.local/bin/hx")},
    config={"config.toml": tracked_copy("~/.config/helix/config.toml")},
)</code></pre>
  </div>
  <div class="tab-pane" data-pane="ts" hidden>
<pre><code class="language-typescript">import { module, githubRelease, symlink, trackedCopy } from "@gripsack/core";
module("helix", {
  fetch: githubRelease({
    repo: "helix-editor/helix",
    asset: "helix-{version}-x86_64-linux.tar.xz",
  }),
  install: { "bin/hx": symlink("~/.local/bin/hx") },
  config: { "config.toml": trackedCopy("~/.config/helix/config.toml") },
});</code></pre>
  </div>
</div>

The core expands the fields into the conventional pipeline:
`fetch → build → install → config → verify → activate`.

## Class style (full control)

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">class style — full control</span>
    <span class="tab-bar">
      <button data-tab="py" class="active" aria-current="true">python</button><button data-tab="ts">typescript</button>
    </span>
  </div>
  <div class="tab-pane" data-pane="py">
<pre><code class="language-python">from gripsack import Module, fetch_step, shell_step, install_step, file_fetch, symlink
class Patched(Module):
    def fetch(self):
        return fetch_step(file_fetch("payloads/hello.tar.gz"))
    def build(self):
        return shell_step("patch -p1 &lt; fix.patch", id="patch")
    def install(self):
        return install_step({"bin/hx": symlink("~/.local/bin/hx")})</code></pre>
  </div>
  <div class="tab-pane" data-pane="ts" hidden>
<pre><code class="language-typescript">import { Module, define, fetchStep, shellStep, installStep, fileFetch, symlink } from "@gripsack/core";
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
define(Patched);</code></pre>
  </div>
</div>

Phase methods return a step or a list of steps; the pipeline chains
them in order — within a phase and across boundaries — so you write
`needs` only for cross-cutting edges. **Phase methods run at eval time
only**: they build data, they never run at build time.

## Ownership modes

| mode | behavior | use for |
|---|---|---|
| `symlink(...)` | store-owned, read-only | disciplined tools |
| `tracked_copy(...)` | copied; drift detected, never silently overwritten | apps that rewrite their configs |
| `merge(...)` | managed block in a shared file | `.bashrc`, `settings.json` other tools also write |
| `template(...)` | rendered per machine at deploy time | hostnames, work vs personal email |

`merge(to, marker=None)` owns exactly one delimited block inside a
file other tools also write — everything outside the markers is never
touched. The block is regenerated wholesale on every apply (drift
*inside* the markers self-heals), prune removes only the block, and
two modules can each own a block in the same file. The comment style
is inferred from the destination (`.jsonc` → `//`, `.vimrc` → `"`,
`.html` → `<!-- -->`, rc files and everything unknown → `#`);
`marker=` overrides the prefix.

`template(to, vars={...})` substitutes `{{ name }}` placeholders in
the payload at deploy time; `{{{{` renders a literal `{{` (payloads
that themselves carry template syntax — helm values, jinja configs —
are expressible). An undefined variable fails the apply loudly, never
renders empty. Compute per-host values at eval time with `facts()` —
the core stays a dumb substituter.

## Steps, resources, retries

Explicit steps carry `needs` (sibling ids or `module:step`), `resources`
(named mutexes — declare them first with `resource("pixi.lock")`; a
typo fails at eval), `verify` contracts, and `retries` overrides. The
action ladder: typed primitives → `run_step` (argv as data) →
`shell_step` (last rung) → `gripfetch-*` plugins for transports.

## Conditionals (hosts, facts, tags)

The runner evaluates the host entrypoint first, then modules — so
modules can read the shared `facts` object (`facts.os`, `facts.arch`,
`facts.libc`, `facts.has("gui")`) and gate whole modules with `when`:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">gating a module on the host</span>
    <span class="tab-bar">
      <button data-tab="py" class="active" aria-current="true">python</button><button data-tab="ts">typescript</button>
    </span>
  </div>
  <div class="tab-pane" data-pane="py">
<pre><code class="language-python">from gripsack import module, when
module("steam", fetch=..., when=when(os="linux", tags=["gui"]))
# class style: the decorator form
@when(os="linux", not_tags=["headless"])
class Steam(Module): ...</code></pre>
  </div>
  <div class="tab-pane" data-pane="ts" hidden>
<pre><code class="language-typescript">import { moduleIf, defineIf } from "@gripsack/core";
moduleIf("steam", { fetch: /* … */ }, { os: "linux", tags: ["gui"] });
// class style
defineIf(Steam, { os: "linux", notTags: ["headless"] });</code></pre>
  </div>
</div>

Per-file conditionals are plain code — different source, same
destination, per host:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">per-file conditionals</span>
    <span class="tab-bar">
      <button data-tab="py" class="active" aria-current="true">python</button><button data-tab="ts">typescript</button>
    </span>
  </div>
  <div class="tab-pane" data-pane="py">
<pre><code class="language-python">module("zed", config={
    ("settings.spaces.json" if facts.has("spaces") else "settings.laptop.json"):
        tracked_copy("~/.config/zed/settings.json"),
})</code></pre>
  </div>
  <div class="tab-pane" data-pane="ts" hidden>
<pre><code class="language-typescript">import { module, trackedCopy, hasTag } from "@gripsack/core";
module("zed", {
  config: {
    [hasTag("spaces") ? "settings.spaces.json" : "settings.laptop.json"]:
      trackedCopy("~/.config/zed/settings.json"),
  },
});</code></pre>
  </div>
</div>

Facts stay curated on purpose: os/arch/libc/tags. Anything beyond that
is eval-time code in your repo — the frontend *is* the extension point.

## Dependencies

`dep("git")` is a runtime edge; `dep("rust", edge=Edge.BUILD)` is an
ephemeral build-only dependency — present while building, GC'd after.
