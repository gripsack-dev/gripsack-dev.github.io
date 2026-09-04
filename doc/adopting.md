# Adopting your dotfiles

The honest walkthrough — no magic, and the two moments where gripsack
deliberately refuses to be magic.

## Start with one directory, not your whole setup

A config-only repo needs nothing but `grip` itself: the frontend
source rides inside the binary, and the only provisioning is the eval
runtime — the first `grip check`/`apply` downloads a pinned,
sha256-verified Deno once (~40MB, cached). And before a repo's code
runs at all, grip asks once: an unfamiliar repo gets a trust prompt
naming exactly what the sandbox allows. `y`, and you're in business.


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

`grip adopt` is the walkthrough as a command ([plan 0015](https://github.com/gripsack-dev/gripsack/tree/main/plan/0015-grip-adopt.md)).
Point it at a live config path; it inspects what it sees, then *asks
you* the ownership question with the semantics laid out — it never
guesses, because only you know whether the app writes its own config.
The safe default is `tracked_copy` (wrong guesses are free there;
`owned` is the informed opt-in). Then it generates the payload +
module + host entry, shows the plan, and touches nothing until you
confirm:

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">adoption is one command — and fully reversible</span></div>
<pre><code class="language-bash">$ grip adopt ~/.config/helix
adopting ~/.config/helix — 2 files, 1.1 kB
  ownership: owned — helix doesn't rewrite its config
  wrote configs/helix/ · modules/helix.ts · hosts/laptop.ts
  prior state will be recorded — rollback restores your original files
apply? [y/N] y
applied — generation 1 active

$ grip rollback
rolled back to generation 0   # your original files are back</code></pre>
</div>

The apply absorbs **exactly** the adopted destinations (scoped
take-over — unrelated drift is never clobbered) and records what every
destination was before gripsack wrote it. Rollback — and undeclaring
the module later — restores the original files, bytes and permission
bits, drift-guarded: edits you make after adopting are yours, and a
rollback keeps them. On a fresh machine adopt first records an empty
**generation 0**, so there's always something to roll back to.

## The safety net under all of it

Adoption is honest because every layer under it has an inverse:

1. **Foreign-path refusal** — gripsack never touches a path it didn't
   deploy unless you say `--take-over`.
2. **Prior capture** — the moment it takes anything over, your
   original bytes (and permission bits) go to a content-addressed
   blob store.
3. **Drift detection** — if you edit a deployed file, gripsack keeps
   your edit and says so; it never silently reverts you.
4. **Run rollback** — an apply that fails mid-graph restores every
   destination it touched before reporting the error.
5. **Generation rollback** — `grip rollback` flips `current` back;
   adopted paths get their originals restored.
6. **Crash recovery** — kill -9 or power loss mid-apply leaves a
   journal; the next apply restores your files before doing anything
   else — and if you edited them after the crash, *your* edit wins.

`grip plan` labels every planned mutation with its reversibility
class, so "what does undoing this mean" is answered before you
confirm, not after.

Writing the module by hand still works, of course — the generated file
is exactly what you'd have written.

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
  `template` with `vars` computed in the host entrypoint from
  `ctx.facts`.

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
