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
| `git(url, rev?)` | live | shallow-fetched and pinned to the resolved commit. No rev follows the default branch at update; a named branch/tag is also frozen to its resolved commit for apply. An explicit commit ID remains fixed |
| `githubRelease(repo, asset, version?, baseUrl?)` | live | resolved release + asset hash, locked; `version` pins the tag (resolved via `/releases/tags/`, never floats). `baseUrl` accepts the bare GHE host (`/api/v3` is appended for you). Private/GHE releases download through the API asset endpoint when a token is bound — tokens are host-scoped the gh-CLI way: `GH_TOKEN`/`GITHUB_TOKEN` only ever go to github.com; `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN` only to enterprise hosts. A download that comes back `text/html` fails as "looks like a login page", not as a hash mismatch |
| `brew(...)` (bottles) | live | update resolves the current stable formula and pins its bottle URL, version and digest. A declared version is a tripwire against that resolution, not a range. Cold apply reuses the locked bottle without asking for today's stable version. Raw bottle layout remains: install paths look like `jq/{version}/bin/jq` |
| `pixi(...)` (conda) | live | the installed primary-package version and the core-harvested payload tree are pinned together; conda bookkeeping is excluded. Update re-resolves; cold apply requests the pinned version and checks the same tree domain. Payloads may embed the machine's fixed private `PIXI_HOME`, so lockfiles remain per-host. Pixi inherits the artifact environment for proxy/CA configuration |

`mise` is deliberately not a fetcher: its backends are mostly GitHub
releases, which `github_release` already covers.

A gzipped *single file* (`.gz` that isn't a tar) stages decompressed as
one executable, named for the asset minus the suffix — alongside
`.tar.gz`/`.tar.xz`/`.zip` archives and bare uncompressed binaries.

## Complete source pins

Since 0.37.0, `grip update` acquires and verifies sources, captures the selected
repo overlay and writes completed pins once after all selected modules succeed.
Source-only merged trees are cached without creating destinations or a generation.
Build recipes and activation hooks do not run. The first warm or cold apply leaves
the completed lockfile unchanged; a failed update preserves its previous bytes.
“One commit” means one user lockfile diff — grip does not make git commits.

Archive downloads are bounded private spools and their full transport digest is
verified before extraction. Decoded bytes, entry counts, metadata and decoder
working memory are admitted separately. Traversal, link escape and unsupported
entries fail before publication. See [acquisition limits](settings/reference.md).
Trusted runtime provisioning captures host network policy before repo build-env
injection; artifact clients capture it afterwards. Pools are shared only within
that command and environment phase.

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

Protocol hosts bound serialized requests (4 MiB), stdout lines (1 MiB),
cumulative stdout/stderr (16 MiB each), retained stderr (64 KiB), and diagnostics
(1,024). Fetch, capability and linter exchanges retain their own success policies.
Deadlines include cleanup; a response never hides later output/exit failures.
The host owns the process group and closes inherited pipes. Prompt OS scheduling
and SIGKILL/reaping are assumptions; descendants deliberately leaving the group
are not a sandbox guarantee. Cleanup failures are reported, never detached.

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
