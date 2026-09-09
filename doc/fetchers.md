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
| `githubRelease({ repo, asset, version?, base_url? })` | live | resolved release and verified asset hash, locked; `version` pins the tag. `base_url` accepts a bare GHE base URL (`/api/v3` is appended). Private/GHE assets use the API endpoint when a token is explicitly bound to its host; see authentication below |
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

### Read-only surveys and layout evidence

`grip update --check` surveys the selected modules even when an individual source
fails. Each module is unchanged, would change, failed, or inapplicable; the final
summary says incomplete when any source failed. Exits are **0** complete/current,
**1** complete/changes available, **2** incomplete or operational failure.
Neither source cache nor lockfile is published by a check.

Source-only install/config and payload-verification paths are checked against the
captured, merged stage **before** normal update publishes its cache or lock.
Known missing paths fail with the original pattern, raw locked tag, expanded path
and observed top-level entries. Recipes and verification programs never run during
update. Recipe-produced layout is deferred until its output exists; `check` and
`plan` use matching cached artifacts without downloading and say when evidence is
unavailable.

### Authentication and request failures

Gripsack retains explicit host-bound credentials. `GITHUB_TOKEN` takes precedence
over `GH_TOKEN` and goes only to github.com/api.github.com. Enterprise credentials
use `GITHUB_ENTERPRISE_TOKEN`, then `GH_ENTERPRISE_TOKEN`, and require
`GH_HOST` (or `GITHUB_HOST`) naming the intended enterprise host:

```sh
export GH_HOST=ghe.example.com
# Supply GH_ENTERPRISE_TOKEN through your trusted secret environment.
grip update --check --host laptop
```

The module's `base_url` is a destination, **not a token grant**. This is stricter
than gh's ability to infer a host from its command/repository context; it is not
exact gh-CLI parity. Missing, unbound/mismatched and rejected bound credentials
get different hints for resolution and locked cold downloads. Correct binding
also determines whether the API asset URL or browser URL is attempted.
Cross-host and HTTPS-to-HTTP redirects do not forward authorization.

An unauthenticated GitHub API primary quota is shared by an egress IP (60/hour),
not by a grip process. A local throttle cannot restore that quota. Confirmed
403/429 rate failures name the reset/cooldown and suggest a public token when
none is bound; other 403s can be permissions or secondary limits. A token is not
a promise to bypass every network/SSO/rate policy.

Grip inherits the caller's environment. Non-interactive SSH does not necessarily
load `/etc/profile.d`; supply secrets explicitly in the calling provisioning
script. Grip never sources profiles, reads gh's credential store, or logs tokens
to compensate for missing environment.

First-party HTTP GETs retry classified transient 500/502/503/504, connection and
interrupted-body failures. The limits are **three policy attempts total**, one
**600s operation deadline**, and at most **30s retry waiting** (normally 1s, then
2s). Server Retry-After/reset lower bounds are never shortened to fit; long or
unknown cooldowns stop with an explanation. Partial transfers restart at zero
without resetting the byte budget. Auth, certificate, invalid metadata,
checksum, archive-safety and local I/O failures are not blindly retried.

Errors identify the URL, policy attempts and stopping reason; URI credentials
and query material are redacted. Pooled-connection recovery inside the HTTP
library is not counted as a separate policy attempt. Built-in local pacing is
30/min for api.github.com and ghcr.io, 60/min for formulae.brew.sh; release CDN
downloads have no built-in domain bucket. User `[throttle]` overrides still win.

## Placeholders

GitHub asset patterns and payload install/config/verify paths accept the version
tokens below. Direct tarball URLs support platform tokens, not a version they
have not resolved. The placeholder set is explicit, not a path-guessing engine:

| placeholder | expands to | example |
|---|---|---|
| `{version}` | raw locked tag in paths; legacy raw-first, then stripped asset search | `ripgrep-{version}-{target}/rg` |
| `{version.bare}` | exactly one leading lowercase `v` removed | `rootle-{version.bare}-{target}/rootle` |
| `{system}` | flake-style platform | `x86_64-linux` |
| `{target}` | the rust triple | `x86_64-unknown-linux-musl` |
| `{arch}` | rust arch | `x86_64` |
| `{arch.go}` | goreleaser arch | `amd64` |
| `{arch.x64}` | node-style arch | `x64` |
| `{os}` | `linux` / `darwin` | `linux` |

For tag `v0.12.1`, `{version}` in a payload path means `v0.12.1`, while
`{version.bare}` means `0.12.1`. A bare token in an asset pattern has only that
exact spelling; it never adds `v` back. Missing/empty required versions and
unsafe expanded paths are errors. Lockfiles still record the raw tag.

Use `{version.bare}` in both the asset pattern and payload key when upstream
v-prefixes its tags but not its archive names/directories. This requires core
0.39.0 or newer; IR remains v3. Unknown tokens are E114 errors, including in
explicit steps.

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
