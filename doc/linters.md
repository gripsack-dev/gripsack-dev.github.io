# Linters

New IR8 workspaces use named `check` outputs attached to profile files,
and task `checks` for invocation postconditions. See the
[0.48 SDK check reference](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md#file-checks-and-manual-tasks).
Those are explicit command checks, not an automatic invocation of the
embedded packs described below.

The `lint` field on this page belongs to the **supported legacy
host/module API**. It checks config shape before deployment; it is not
a workspace `file` option or a complete schema validator for every tool.

Linters are **data**: every shipped linter is a versioned data pack
embedded in grip (`crates/griplint/packs`, key tables as TOML) checked
by the in-crate engine **in-process** — no venv, no provisioning, no
plugin lifecycle. `lint: "name"` travels in legacy module IR;
`grip check` and `grip apply` run the linter with no additional runtime
for embedded packs. External `griplint-*` executables retain the
protocol path for formats not covered by the data engine.

The 0.48 source contains the 23 embedded packs below. A pack covers its
recorded versions and rules, not every upstream setting or future version.

## Coverage

<div class="lint-stats">
  <span><b>23</b> available</span>
</div>

<p class="lint-legend"><span class="lg lg-a"></span>included in core 0.48</p>

<div class="lint-grid">
  <a class="lint-tool lt-reference" style="--lt:var(--green)" href="https://github.com/gripsack-dev/gripsack/tree/core-v0.48.0/crates/griplint/packs"><span class="lt-name">helix</span><span class="lt-status">reference</span></a>
  <span class="lint-tool lt-available" style="--lt:var(--blue)"><span class="lt-name">alacritty</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--peach)"><span class="lt-name">starship</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--yellow)"><span class="lt-name">yazi</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--mauve)"><span class="lt-name">mise</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--teal)"><span class="lt-name">jj</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--red)"><span class="lt-name">atuin</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--blue)"><span class="lt-name">glow</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--peach)"><span class="lt-name">superfile</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--yellow)"><span class="lt-name">zola</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--mauve)"><span class="lt-name">bottom</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--teal)"><span class="lt-name">git-cliff</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--red)"><span class="lt-name">broot</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--blue)"><span class="lt-name">ruff</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--peach)"><span class="lt-name">rio</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--yellow)"><span class="lt-name">harlequin</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--mauve)"><span class="lt-name">television</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--teal)"><span class="lt-name">procs</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--red)"><span class="lt-name">bacon</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--blue)"><span class="lt-name">claude-code</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--peach)"><span class="lt-name">zed</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--yellow)"><span class="lt-name">gh-dash</span></span>
  <span class="lint-tool lt-available" style="--lt:var(--mauve)"><span class="lt-name">tuicr</span></span>
</div>

Available means a data pack in the
[0.48 source](https://github.com/gripsack-dev/gripsack/tree/core-v0.48.0/crates/griplint/packs),
not a promise of complete config validation.

## Using a linter

For legacy modules, first-party packs need no registration:
`lint: "helix"` selects the embedded pack. External plugins register
in `env.toml`; opt in from the module either way.

```toml
# Only needed for an external linter:
[linters.internal]
path = "/opt/bin/griplint-internal"     # explicit executable — the out-of-tree form
```

```typescript
import { module, symlink } from "@gripsack/core";

export default module("yazi", {
  config: { "configs/yazi/yazi.toml": symlink("~/.config/yazi/yazi.toml") },
  lint: "yazi",
});
```

- `package` is a plugin-store ref `"owner/repo@tag"`: grip downloads
  the release binary, verifies it against the mandatory sha256
  sidecar, and receipts it into `$GRIPSACK_HOME/plugins/` — the tag
  is the pin. `path` is the explicit executable for development.
- `lint = "<name>"` must resolve against the registry: an
  unregistered name is a hard eval error with the module-line span,
  never a silent skip. There is deliberately no PATH-discovery
  fallback — discovery is how configs end up silently unlinted on one
  machine and linted on another.
- `lint=` is the entire opt-in; there are no per-entry file lists. The
  linter owns the tool's layout knowledge: one `griplint-yazi` covers
  `yazi.toml`, `keymap.toml`, and `theme.toml`, and ignores what it
  doesn't recognize.

## The command surface

For legacy modules, the core runs linting after evaluation and semantic
admission. These commands do not have identical side effects:

| command | behavior |
|---|---|
| `grip check` | eval + IR sema + linters; no destination deployment or payload build, but source capture, private evaluation receipts and external-plugin provisioning can occur |
| `grip plan` | validates frozen inputs and reports the diff against the current generation; use explicit `grip update` to refresh pins |
| `grip apply` | an error-severity lint diagnostic fails eval before anything stages |

Linters check **static shape**. Legacy `verify` contracts and workspace
named checks execute commands at their declared lifecycle stages.
`grip check` is not a blanket execution of all named workspace checks.

## The lint flow

Embedded packs run in-process. External linters use the protocol below;
both return diagnostics rendered by the core.

a typo'd key fails `grip check` with a span — before anything is
staged, before the tool ever runs:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">grip check — legacy eval + sema + linters</span></div>
<pre><span class="err">error[griplint-helix/A01]</span>: unknown key [editor] <span class="s">'scrollof'</span>
  <span class="loc">--&gt;</span> <span class="loc">/home/you/env/configs/helix/config.toml:4:1</span>
   <span class="gutter">|</span>
 <span class="loc">4</span> <span class="gutter">|</span> scrollof = 5
   <span class="gutter">|</span> <span class="err">^ not a real key</span>
  <span class="hlp">help</span>: did you mean <span class="s">'scrolloff'</span>?</pre>
</div>

## Writing a linter

A linter is a plain executable speaking NDJSON over stdio — one
request per module–linter pair:

```json
{"op": "lint", "paths": ["configs/yazi/yazi.toml", "configs/yazi/keymap.toml"],
 "tool_version": "25.5.31"}
```

- `paths` is the legacy module's prepared config source set, post-`tree()`
  expansion, read from the captured source bundle.
- `tool_version` comes from the host lockfile pin — the lock that pins
  the binary also pins the config schema. Unpinned, the linter uses
  its latest schema and warns.
- Diagnostics come back in the shared shape — same snippet, colors,
  and codespacing as every other gripsack diagnostic. Codes are
  namespaced `griplint-<tool>/<code>` (e.g. `griplint-yazi/A01`); the
  core's `E0xx` range stays reserved. Plugins serialize; only the core
  renders — there is no second renderer.
- Unknown files are ignored, never errors. A linter that chokes on a
  layout it doesn't recognize is a bad linter, not a bad config.
- Death is never silent: a linter that crashes, hangs, or emits
  garbage surfaces as a diagnostic, not a missing check.
The contract made executable:
[griplint-conformance](https://github.com/gripsack-dev/griplint-conformance)
and
[gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance)
— run your plugin against the suite and the envelope stops being
prose.

## Where linters live

In the gripsack repo as data:
[`crates/griplint/packs`](https://github.com/gripsack-dev/gripsack/tree/core-v0.48.0/crates/griplint/packs)
— TOML packs keyed by tool version, read by the in-crate engine.
External executables use the protocol above and run as trusted native
code, not inside the TypeScript evaluator sandbox. A successful lint
does not establish runtime safety or complete upstream compatibility.
