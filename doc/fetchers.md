# Fetchers

How gripsack gets bytes. Two tiers: in-tree fetchers maintained in the
core, and `gripfetch-*` plugins for everything else. Version pinning
always lands in the lockfile (`grip update` re-resolves; `apply`
verifies).

## In-tree (first-class)

| fetcher | status | pinning |
|---|---|---|
| `file_fetch(path)` | live | content hash |
| `tarball(url, sha256)` | live | pinned sha256, verified before the store |
| `git(url, rev)` | live | the rev is immutable; shallow-fetched |
| `github_release(repo, asset)` | 0.2 | resolved release + asset hash, locked |
| `brew(...)` (bottles) | 0.2/0.3 | bottle hash, locked |
| `pixi(...)` (conda) | 0.3 | package hashes from the pixi resolution, locked |

`mise` is deliberately not a fetcher: its backends are mostly GitHub
releases, which `github_release` already covers.

## Out-of-tree (plugins)

A `gripfetch-<name>` executable on your `PATH` (or wired via
`[fetchers.<name>]` in `env.toml`), speaking NDJSON over stdio:

- `fetch {args, dest_dir, locked}` → bytes into `dest_dir`, responds
  `{sha256}`
- `capabilities` → features + rate budget (the engine throttles to it)

The core hash-verifies every returned byte against the lockfile before
it enters the store — a plugin can be wrong or malicious and the worst
outcome is a failed apply, never a poisoned store.

This is the home for: distro packages (apt/dnf — their pinning is repo
snapshots and maintainer scripts, not ours to own), internal company
registries, and anything bespoke. If your registry just needs
*resolution* logic ("latest artifact X" → pinned URL), that's even
simpler — an eval-time resolver in your env repo's `lib/`, no plugin
required.

## The ladder, always

1. built-in fetcher arguments (`base_url` covers GitHub Enterprise),
2. eval-time resolver (your Python/TS code),
3. `gripfetch-*` plugin (bespoke transport).

Full design: [plan/0002](https://github.com/gripsack-dev/gripsack/blob/main/plan/0002-sourcing.md).
