# Linters

Config linters are eval-time validation plugins: `griplint-*`
executables that check your config files against the tool's own
schema before anything is staged. A typo'd key in `yazi.toml` deploys
cleanly today and fails at tool runtime, in a different terminal, an
hour later — linters close that gap at eval, where the error points
at the offending line.

Status: landing next — the implementation PR is open.
## Coverage

One reference linter ships first — helix — with the tools the dotfiles
crowd actually edits queued behind it, sorted by github stars. The
long tail is yours to claim.

<div class="lint-stats">
  <span><b>1</b> reference</span>
  <span><b>49</b> planned</span>
  <span><b>∞</b> the long tail</span>
</div>

<div class="lint-grid">
  <a class="lint-tool lt-reference" style="--lt:var(--green)" href="https://github.com/gripsack-dev/griplint-py"><span class="lt-name">helix</span><span class="lt-status">reference</span></a>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">deno</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">zed</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">lazygit</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">alacritty</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">ghostty</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">starship</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">lazydocker</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">yazi</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">Hyprland</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">zellij</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">kitty</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">k9s</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">btop</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">glances</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">delta</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">mise</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">jj</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">atuin</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">niri</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">glow</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">biome</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">fastfetch</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">oh-my-posh</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">superfile</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">gitui</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">zola</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">rofi</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">lsd</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">pre-commit</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">bottom</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">tmuxinator</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">gh-dash</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">posting</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">git-cliff</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">eza</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">waybar</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">broot</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">ruff</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">lf</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">rio</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">harlequin</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">television</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">procs</span></span>
  <span class="lint-tool" style="--lt:var(--peach)"><span class="lt-name">taskwarrior</span></span>
  <span class="lint-tool" style="--lt:var(--yellow)"><span class="lt-name">dunst</span></span>
  <span class="lint-tool" style="--lt:var(--mauve)"><span class="lt-name">newsboat</span></span>
  <span class="lint-tool" style="--lt:var(--teal)"><span class="lt-name">editorconfig</span></span>
  <span class="lint-tool" style="--lt:var(--red)"><span class="lt-name">bacon</span></span>
  <span class="lint-tool" style="--lt:var(--blue)"><span class="lt-name">zathura</span></span>
  <a class="lint-tool lt-more" href="https://github.com/gripsack-dev/griplint-py/issues?q=label:linter"><span class="lt-name">+ more</span><span class="lt-status">help wanted ↗</span></a>
</div>

Every planned tool has an open tracking issue — pick one up, or file
the one your dotfiles need.

## Using a linter

Two halves: register the plugin in `env.toml`, opt in from the module.

```toml
[linters.yazi]
package = "griplint-yazi==1.2.0"      # provisioned into the frontend venv

[linters.internal]
path = "/opt/bin/griplint-internal"   # explicit override
```

```python
module("yazi", ..., lint="yazi")
```

- `package` requires an `==` pin. Pins join the venv hash, so the same
  env.toml yields identical linter behavior on every machine. Python
  linters are provisioned automatically — no PATH mutation, no
  separate tool installs. Non-Python linters keep the `path` form.
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

Linting runs wherever eval runs, so every command that evaluates gets
diagnostics for free:

| command | behavior |
|---|---|
| `grip check` | eval + IR sema + linters, then stop: render every diagnostic, exit code = validity, zero side effects — the tight config-editing loop and the CI gate for your dotfiles repo |
| `grip plan` | check + lockfile + diff vs the current generation — "what would change" includes "and by the way, this is broken" |
| `grip apply` | an error-severity lint diagnostic fails eval before anything stages |

Linters are **static shape** (does this key exist in yazi 25.x);
`verify` contracts are **runtime smoke** (does the deployed thing
work). A mode that shells out to the tool itself belongs to the verify
side — the two stay apart.

## Writing a linter

A linter is a plain executable speaking NDJSON over stdio — one
request per module–linter pair:

```json
{"op": "lint", "paths": ["configs/yazi/yazi.toml", "configs/yazi/keymap.toml"],
 "tool_version": "25.5.31"}
```

- `paths` is the module's config source set, post-`tree()` expansion;
  repo files are linted in place.
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

## Where linters live

Linters are plain Python with vendored schemas per tool version. The
`griplint-py` monorepo holds them — one PyPI package per tool
(`griplint-yazi`, `griplint-helix`, …), each shipping a console
script. The tables are community-maintained, and the north star is
DefinitelyTyped: the tool's owners eventually own their linter, and
gripsack just provides the envelope and the renderer.

Full design: [plan/0010](https://github.com/gripsack-dev/gripsack/blob/main/plan/0010-plugin-provisioning.md)
and [plan/0011](https://github.com/gripsack-dev/gripsack/blob/main/plan/0011-validation-plugins.md).
