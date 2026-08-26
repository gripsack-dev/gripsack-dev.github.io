# Adopting your dotfiles

The honest walkthrough — no magic, and the two moments where gripsack
deliberately refuses to be magic.

## Start with one directory, not your whole setup

```bash
grip init my-env && cd my-env
```

You get a working repo: `env.toml`, a host entrypoint named after this
machine, a tiny `hello` module that deploys one file into
`~/.config/hello/`, and a commented tour of the features. Apply it:

```bash
grip check && grip apply
```

Then look at `~/.config/hello/hello.toml` — it's a symlink into the
store. Edit the file in the repo, apply again, watch the generation
flip. That's the whole mechanism; everything else is detail.

## Move one real tool over

Pick the boring one — the tool whose config never fights back (helix,
git, starship). Copy its config directory into the repo and declare it:

```python
from gripsack import module, tree
from gripsack.entries import Ownership

module(
    "helix",
    config=tree("configs/helix", "~/.config/helix", mode=Ownership.OWNED),
)
```

`tree()` expands the directory into one entry per file. `OWNED` means
symlinks into the store: your repo is the only editor, and `git diff`
is your changelog.

**The first apply will refuse.** The destination already exists and
gripsack didn't put it there — it will not clobber a foreign path.
That refusal is the feature; the handover is explicit:

```bash
grip apply --take-over   # once, per existing path
```

After that, applies are clean and the second one is a satisfied no-op.

## The ownership question is the whole game

For each tool, one question: *does this app ever rewrite its own
config?*

- **Never** (helix, git, tmux) → `owned` symlinks.
- **Sometimes** (zed, VS Code, most GUI apps) → `tracked_copy`: a real
  file; gripsack detects drift and *keeps your edit* instead of
  pretending the app behaves.
- **Shared files** (`.bashrc`, `.profile`) → `merge`: gripsack owns one
  delimited block, everything outside the markers is never touched.
- **Same file, per-host values** (work email vs personal) →
  `template` with `vars` computed from `facts()`.

## What stays outside (on purpose)

You don't have to migrate your packages. brew/apt/pixi keep managing
binaries; gripsack manages `~/.config` — and you can adopt binary
fetching later, tool by tool, when the pinned-download story is worth
it. Fish users: your universal variables and conf.d are yours; a
`merge` block in `~/.bashrc`-style files is the seam.

## When it breaks

`grip doctor` checks the runtime, `grip why-owns <path>` answers "which
module deployed this", and `grip rollback` flips the whole environment
back to the previous generation. If a linter crashes, that's a warning,
not a failed apply — your tools' problems are not your outage.

When you're ready to move a whole tree, the `gripsack-adopt` skill
teaches an agent to do the inventory and the interview with you:
`cp -r skills/gripsack-adopt ~/.claude/skills/` (see
[skills](skills.md)).
