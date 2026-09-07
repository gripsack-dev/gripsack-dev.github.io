# Settings reference

Every configuration key, where it lives, and what it does. For the
friendly tour see [settings](settings.md); the design rationale is in
[plan/0005](plan/0005-frontends-and-configuration.md).

## Files and precedence

| layer | file | committed? |
|---|---|---|
| repo | `env.toml` (env repo root) | yes |
| user | `~/.config/gripsack/config.toml` | no |

Precedence, later wins: built-in defaults < user config < repo
`env.toml` < environment variables < CLI flags. Configuration is pure
data and is always read before module evaluation.

## `[env]` — env.toml only

| key | type | default | what |
|---|---|---|---|
| `name` | string | — | human name for the env (used in output) |
| `default_host` | string | — | the host entrypoint when no `--host` is given and the machine's hostname matches nothing in `hosts/` — role-named host files for ephemeral containers with random hostnames. An unmatched host with a non-empty `hosts/` is an error, not silently-empty tags |

`frontend` is gone (0013): TypeScript is the only frontend and needs
no declaration — `hosts/*.ts` and `modules/*.ts` are it. A stale
`frontend = "python"` fails with a migration hint, not a mystery.

## `[eval]` — env.toml only

| key | type | default | what |
|---|---|---|---|
| `env` | string map | `{}` | build-time environment injected into the apply process for the run's duration — build steps, fetchers, and plugins inherit it (`SSL_CERT_FILE` is the canonical case). The sandboxed eval sees none of it |

## `[fetchers.<name>]` — env.toml or user config

| key | type | default | what |
|---|---|---|---|
| `plugin` | string | — | fetcher plugin for this source; default discovery is `gripfetch-<name>` on `PATH` |
| `package` | string | — | provision the fetcher from a GitHub release: `owner/repo@tag`. grip manages the lifecycle — downloaded at eval, sha256-verified against the mandatory sidecar asset, receipted into `$GRIPSACK_HOME/plugins/`; the tag is the pin. Mutually exclusive with `plugin` |

The same form works for linter plugins: `[linters.<name>] package =
"owner/repo@tag"` provisions an executable `griplint-<name>` —
sha256-verified, receipted, exactly like a fetcher. A fresh install
prints its source — a new plugin runs with your user rights.

Repo entries override user entries of the same name.

## `[throttle]` — env.toml only

Rate budgets per domain, as `"domain" = "N/unit"` (units: `s`, `min`,
`hr`). The engine runs a token bucket per domain and blocks until a
token is available; bucket state persists in
`$GRIPSACK_HOME/throttle.json`, so back-to-back applies share one
budget.

```toml
[throttle]
"api.github.com" = "30/min"
```

Precedence: built-in defaults for the internal fetchers' registries
(`api.github.com`, `ghcr.io`, `formulae.brew.sh`) < budgets declared
by a fetcher via the `capabilities` op < `[throttle]` here. Downloads
from release CDNs are not throttled — rate limits live on API
endpoints.

## `[settings]` — env.toml or user config

| key | type | default | what |
|---|---|---|---|
| `keep_generations` | integer | ∞ | generations retained before `grip gc` reclaims store paths |
| `acquisition_jobs` | positive integer | 2 | maximum simultaneous payload acquisitions, independent of module `--jobs` |
| `download_limit_bytes` | positive integer | 536870912 | streamed download cap per payload (512 MiB) |
| `expanded_limit_bytes` | positive integer | 4294967296 | expanded stream/tree cap per payload (4 GiB) |
| `archive_entry_limit` | positive integer | 100000 | archive/materialized-tree entry cap |
| `decoder_memory_bytes` | positive integer | 134217728 | backend decoder working-memory/window budget (128 MiB); archive metadata is separately admitted within a bounded budget |

Limits are layered like other settings: the repo wins over the user file.
Zero does not mean unlimited; invalid values fail configuration admission.
Downloads are hashed into private disk spools and verified before extraction.
Exceeding a limit is an error, never silent truncation or partial publication.

## Environment variables

| var | what |
|---|---|
| `GRIPSACK_HOME` | base directory for store, generations, and the `current` symlink (default: `$XDG_DATA_HOME/gripsack` or `~/.local/share/gripsack`) |
| `GRIPSACK_BIN` | path to the `grip` binary (used by the e2e harness) |
| `GRIPSACK_DENO` | bring-your-own eval runtime: a deno binary — wins over a deno on `PATH` and the pinned provisioned download |
| `GRIPSACK_TRUST_ALL` | `=1` skips the repo trust prompt before eval — the CI escape hatch |
| `SSL_CERT_FILE` | the corporate CA bundle — grip's rustls-based fetching honors it and the tools grip spawns inherit it, so TLS-intercepting proxies verify; set it before invoking grip |
| `HTTPS_PROXY` / `NO_PROXY` | corporate proxy support; the system CA roots are trusted |
| `XDG_DATA_HOME` | honored for the default `GRIPSACK_HOME` |

## CLI surface

```bash
grip init [DIR]                     # scaffold an env repo from the embedded template
grip adopt <path>                   # interview-style adoption of an existing config — records priors, reversible
grip apply [--host H] [MODULE...]   # fetch, build, deploy — one new generation
grip plan [--host H] [MODULE...]    # show what apply would change
grip check                         # eval + sema + linters; exit code = validity
grip update [MODULE]               # acquire sources and finalize pins without deployment
grip update --check [MODULE]       # resolve in scratch; exit 1 if any pin would move
grip rollback [N]                   # flip current back to generation N
grip generations                    # list generations and their status
grip gc                             # collect unreferenced store paths
grip gc --dry-run                  # show what gc would reclaim
grip why-owns <path>                # which module owns a deployed path
grip doctor                         # check deno and the frontend eval actually resolves
grip trust list/add/remove          # the repo trust list — the gate before any eval
grip store-verify [--repair]         # re-hash store paths against expectations
grip self-update                    # update grip itself from the latest core release
```

`update` completes source pins in one lockfile write. Source-only merged
artifacts become an unrooted cache: GC may evict them before the first apply,
and a pinned cold apply reconstructs them without another lockfile change.
Retained generations continue to protect their artifact roots. Build recipes
and hooks are never executed by update.

`update --check` performs resolution and acquisition in private scratch without
publishing source-cache artifacts or writing the lockfile. Exit 0 means current;
exit 1 means at least one pin would change (errors also fail). The command can
use the network; normal eval/runtime provisioning and run-log bookkeeping still
apply. It neither deploys nor runs recipes/hooks.

Self-update holds a per-executable lock and rechecks the installed version,
so an older waiting updater cannot downgrade it. Publication checks mode,
syncs bytes, renames, then syncs the directory. An error after rename reports
that the executable changed; it never attempts an automatic rollback.

All shipped; the config schema on this page is their stable contract.
