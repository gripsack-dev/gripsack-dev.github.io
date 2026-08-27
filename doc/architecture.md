# Architecture

How gripsack turns one git repository into your entire environment —
packages from any source, dotfiles included — on any machine, with
rollback. This page is the friendly tour; the design docs under
[plan/](plan/) have the full details and the reasoning.

![gripsack architecture: eval row (env repo → frontend → IR → lockfile) with linter plugins validating configs at eval, feeding the execute row (core → store → generations → $HOME), with fetcher plugins below](architecture.svg)

## The two halves

gripsack is a compiler, and it keeps its two halves strictly separate:

- **Eval** happens in *your* repo, in *your* language (Python or TypeScript, both shipped), with *your* credentials. Modules — plain code using a
  typed library — describe what you want: where a tool comes from, how
  to build it, which config files it owns. Evaluation emits **IR**, a
  JSON graph where every node carries a *span* pointing back at the
  exact line of your code that produced it.
- **Execute** is the `grip` binary — one static Rust executable. It
  never evaluates code, never sees your credentials, and only consumes
  IR. It parses, validates, resolves against the lockfile, builds a
  plan, and executes it as a DAG into a hash-addressed **store**.

The payoff of the split: `grip plan` can show you exactly what would
change without changing anything, errors point at your source instead of
at JSON, and the core stays a small, boring, auditable program.

## Modules and sources

Everything is a **module** — a tool, a font, a set of dotfiles. A module
declares typed steps, not scripts: a **source** (GitHub release,
tarball, git, cargo, …), an optional build, where its files go, and
which config files it manages. Modules depend on modules; build-only
dependencies are *ephemeral* — a Rust toolchain used to compile
something doesn't linger in your profile afterward.

When a source is unusual — your company's internal registry — the
sourcing ladder keeps the core small:

1. **built-in fetcher arguments** (`base_url` covers GitHub Enterprise),
2. **resolvers** — eval-time code in your repo that turns "latest
   artifact X" into a pinned URL + hash (the skill travels with your
   dotfiles),
3. **fetchers** — `gripfetch-*` plugins for genuinely bespoke
   transports, with the core hash-verifying every byte they return.

## Dotfiles, first-class

Config files are deployed per **ownership mode**, chosen per file:

| mode | what it means | use it for |
|---|---|---|
| `owned` | store-owned symlink, read-only | disciplined tools (helix, git) |
| `tracked-copy` | copied out; drift detected next apply | apps that rewrite their own configs |
| `merge` | managed block inside a shared file | `.bashrc`, `.profile` |
| `template` | rendered per machine at activation | hostnames, work vs personal |

You don't have to migrate your packages to use this. A module with no
source at all — just configs — is a first-class setup: brew/apt keep
managing binaries, gripsack manages `~/.config`, and you get versioned
dotfiles with rollback. See
[plan/0006 — gradual migration](plan/0006-gradual-migration.md).

## Generations and rollback

Every apply — one module or the whole graph — builds a complete new
**generation**: an immutable tree of symlinks into the store. Activation
is a single atomic rename (`current → generations/N`), so nothing is
ever half-applied, and rollback is flipping one symlink back. Because
the profile's bin directory is a fixed PATH entry, a flip takes effect
instantly — no shell reload.

**What rollback covers, exactly.** Transactional per generation: store
payloads, symlinks, tracked copies, managed blocks inside foreign
files, and the exported env profile — all restored to the previous
generation's bytes. Not transactional: side effects that already ran
— a service an activation adapter already enabled stays enabled (a
new apply with the adapter removed disables it), and downloads stay
downloaded. The flip is the environment; the world outside it is
yours.

Reproducibility is **pinned inputs and reproducible deployment**, not
hermetic builds: URLs, revisions, and content hashes are locked per
host at resolve time, so machine B deploys what machine A deployed.
gripsack has no sandbox — a shell build step can observe ambient
machine state; hermetic builds are Nix's guarantee, honestly theirs.

## Errors that point at your code

Every IR node carries a span — file, line, column of the module code
that emitted it (the same trick React uses for JSX error stacks). The
core's compiler passes collect structured diagnostics with stable codes:

```diag
error[E101]: module "helix" depends on unknown module "git"
  --> modules/helix.py:4:1
```

Tomorrow's LSP is a thin shim over these same passes — the analysis is
already done, spans and all. Details:
[plan/0004 — rich IR & passes](plan/0004-rich-ir-and-passes.md).

## Where things live

| path | what |
|---|---|
| `~/.local/share/gripsack/store/` | immutable, hash-addressed payloads |
| `~/.local/share/gripsack/generations/` | one directory per generation |
| `~/.local/share/gripsack/current` | the symlink that IS your profile |
| `~/.config/gripsack/config.toml` | machine-local user config |
| your repo's `env.toml` | the committed, self-describing env config |

`GRIPSACK_HOME` overrides the base directory. Nothing outside your home
is ever touched: no root, no daemon.
