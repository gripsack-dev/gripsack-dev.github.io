# Fetchers

How gripsack gets bytes. Two tiers: in-tree fetchers maintained in the
core, and `gripfetch-*` plugins for everything else. Version pinning
always lands in the lockfile (`grip update` re-resolves; `apply`
verifies).
![the fetcher plugin flow: a module's pluginFetch call with opaque args → the core discovers the executable (env.toml path → the plugin store → PATH) and sends one JSON request on stdin → the gripfetch-artifactory plugin writes bytes and streams NDJSON back → the core hash-verifies the bytes against the lockfile before anything enters the store, with the in-tree fetchers below](fetchers-flow.svg)

## In-tree (first-class)

| fetcher | status | pinning |
|---|---|---|
| `fileFetch(path)` | live | content hash |
| `tarball(url, sha256)` | live | pinned sha256, verified before the store |
| `git(url, rev?)` | live | a pinned rev is immutable and shallow-fetched; no rev floats the default branch's HEAD — pinned into the lockfile at resolve time, `grip update` moves it |
| `githubRelease(repo, asset, version?, baseUrl?)` | live | resolved release + asset hash, locked; `version` pins the tag (resolved via `/releases/tags/`, never floats). `baseUrl` accepts the bare GHE host (`/api/v3` is appended for you). Private/GHE releases download through the API asset endpoint when a token is bound — tokens are host-scoped the gh-CLI way: `GH_TOKEN`/`GITHUB_TOKEN` only ever go to github.com; `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN` only to enterprise hosts. A download that comes back `text/html` fails as "looks like a login page", not as a hash mismatch |
| `brew(...)` (bottles) | live | bottle hash, locked; **floats to the current formula** — the API only serves stable, so `version=` is a tripwire that fails at resolve (`grip update` to move), never a range. Payload is the raw bottle layout: install paths look like `jq/{version}/bin/jq` (`{version}` substitutes from the lock) |
| `pixi(...)` (conda) | live | package hashes from the pixi resolution, locked; `grip update` re-resolves. Two per-host caveats: conda payloads embed the machine's `PIXI_HOME` path, so the same package can pin to different hashes on different hosts (lockfiles are per host by design — this is why), and behind a TLS-intercepting proxy pixi uses its bundled roots only — export `SSL_CERT_FILE` (it inherits it) so the corporate CA verifies |

`mise` is deliberately not a fetcher: its backends are mostly GitHub
releases, which `github_release` already covers.

A gzipped *single file* (`.gz` that isn't a tar) stages decompressed as
one executable, named for the asset minus the suffix — alongside
`.tar.gz`/`.tar.xz`/`.zip` archives and bare uncompressed binaries.

## Placeholders

Asset patterns, tarball URLs, and install/verify keys expand a small,
explicit placeholder set — no pretend-universal naming:

| placeholder | expands to | example |
|---|---|---|
| `{version}` | the locked tag (both `v25.07` and `25.07` match assets) | `helix-{version}-x86_64-linux.tar.xz` |
| `{system}` | flake-style platform | `x86_64-linux` |
| `{target}` | the rust triple | `x86_64-unknown-linux-musl` |
| `{arch}` | rust arch | `x86_64` |
| `{arch.go}` | goreleaser arch | `amd64` |
| `{arch.x64}` | node-style arch | `x64` |
| `{os}` | `linux` / `darwin` | `linux` |

`{version}` in an install or verify key substitutes the locked tag —
that's how you reach into a versioned top-level directory inside an
archive (`ripgrep-{version}-{target}/rg`). A typo'd placeholder is a
check-time error with a did-you-mean (E114), never a 404 at fetch.

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
it enters the store — a plugin cannot poison the store. Be precise
about what that means: **a `gripfetch-*` executable is
trusted code running with your user privileges.** Hash verification
protects store contents, not the host — the plugin process can read
files, inherit environment variables, and open network connections.
Treat a fetcher plugin exactly as you would any binary you install.
Writing one? The contract made executable:
[gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance)
— the suite every plugin runs against.

The reference implementation is
[gripfetch-apt](https://github.com/gripsack-dev/gripfetch-apt) —
distro packages via the host's apt (wraps, never reimplements; honors
the host's mirrors), conformance-gated, and provisionable through the
plugin lifecycle (`package = "gripsack-dev/gripfetch-apt@0.1.0"`).

This is also the home for internal company registries and anything
bespoke. If the transport is fine but *resolution* isn't ("latest
artifact X" → pinned URL + hash), that is planned as its own plugin
kind — `gripresolve-*` executables, specified in
[plan/0013 D8](https://github.com/gripsack-dev/gripsack/blob/main/plan/0013-constrained-evaluation.md)
and built next; today the built-ins resolve at lock/update time.

## The ladder, always

1. built-in fetcher arguments (`base_url` covers GitHub Enterprise),
2. `gripfetch-*` plugin (bespoke transport).

Full design: [plan/0002](https://github.com/gripsack-dev/gripsack/blob/main/plan/0002-sourcing.md).
