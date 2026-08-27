# Fetchers

How gripsack gets bytes. Two tiers: in-tree fetchers maintained in the
core, and `gripfetch-*` plugins for everything else. Version pinning
always lands in the lockfile (`grip update` re-resolves; `apply`
verifies).
![the fetcher plugin flow: a module's plugin_fetch call with opaque args → the core discovers the executable (env.toml path → provisioned venv bin → PATH) and sends one JSON request on stdin → the gripfetch-artifactory plugin writes bytes and streams NDJSON back → the core hash-verifies the bytes against the lockfile before anything enters the store, with the in-tree fetchers below](fetchers-flow.svg)

## In-tree (first-class)

| fetcher | status | pinning |
|---|---|---|
| `file_fetch(path)` | live | content hash |
| `tarball(url, sha256)` | live | pinned sha256, verified before the store |
| `git(url, rev)` | live | the rev is immutable; shallow-fetched |
| `github_release(repo, asset, version=, base_url=)` | live | resolved release + asset hash, locked; `version=` pins the tag (resolved via `/releases/tags/`, never floats). `base_url` accepts the bare GHE host (`/api/v3` is appended for you). Private/GHE releases download through the API asset endpoint when a token is bound — tokens are host-scoped the gh-CLI way: `GH_TOKEN`/`GITHUB_TOKEN` only ever go to github.com; `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN` only to enterprise hosts. A download that comes back `text/html` fails as "looks like a login page", not as a hash mismatch |
| `brew(...)` (bottles) | live | bottle hash, locked; **floats to the current formula** — the API only serves stable, so `version=` is a tripwire that fails at resolve (`grip update` to move), never a range. Payload is the raw bottle layout: install paths look like `jq/{version}/bin/jq` (`{version}` substitutes from the lock) |
| `pixi(...)` (conda) | live | package hashes from the pixi resolution, locked. Two caveats: `grip update` can't re-resolve pixi modules yet (they stay pinned until then — pin deliberately), and behind a TLS-intercepting proxy pixi uses its bundled roots only — export `SSL_CERT_FILE` (it inherits it) so the corporate CA verifies |

`mise` is deliberately not a fetcher: its backends are mostly GitHub
releases, which `github_release` already covers.

A gzipped *single file* (`.gz` that isn't a tar) stages decompressed as
one executable, named for the asset minus the suffix — alongside
`.tar.gz`/`.tar.xz`/`.zip` archives and bare uncompressed binaries.

## Out-of-tree (plugins)

A `gripfetch-<name>` executable — declared in `env.toml` and
provisioned by grip's plugin lifecycle, or hand-placed on `PATH` —
speaking NDJSON over stdio:

<div class="plugin-cards">
  <a class="plugin-card" href="fetchers/apt.html">
    <span class="pc-name">apt</span>
    <span class="pc-blurb">distro packages via the host's apt — wraps, never reimplements; enterprise mirrors inherit free</span>
  </a>
</div>

- `fetch {args, dest_dir, locked}` → bytes into `dest_dir`, responds
  `{sha256}`
- `capabilities` → `{"capabilities": {"throttle": {"registry.example.com":
  "60/min"}}}` — the fetcher declares its registry's rate budget; the
  engine runs a token bucket per domain and throttles to it. Budgets
  live in fetchers because the fetcher knows its registry; `[throttle]`
  in env.toml outranks any declaration. A plugin that predates the op
  is tolerated (no declared budgets) but must not pretend success.

The core hash-verifies every returned byte against the lockfile before
it enters the store — a plugin can be wrong or malicious and the worst
outcome is a failed apply, never a poisoned store.
Writing one? The contract made executable:
[gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance)
— the suite every plugin runs against.

The reference implementation is
[gripfetch-apt](https://github.com/gripsack-dev/gripfetch-apt) —
distro packages via the host's apt (wraps, never reimplements; honors
the host's mirrors), conformance-gated, and provisionable through the
plugin lifecycle (`package = "gripsack-dev/gripfetch-apt@0.1.0"`).

This is also the home for: internal company
registries, and anything bespoke. If your registry just needs
*resolution* logic ("latest artifact X" → pinned URL), that's even
simpler — an eval-time resolver in your env repo's `lib/`, no plugin
required.

## The ladder, always

1. built-in fetcher arguments (`base_url` covers GitHub Enterprise),
2. eval-time resolver (your Python/TS code),
3. `gripfetch-*` plugin (bespoke transport).

Full design: [plan/0002](https://github.com/gripsack-dev/gripsack/blob/main/plan/0002-sourcing.md).
