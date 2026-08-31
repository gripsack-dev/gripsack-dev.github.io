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
grip update [MODULE]               # re-resolve pins into the lockfile
grip rollback [N]                   # flip current back to generation N
grip generations                    # list generations and their status
grip gc                             # collect unreferenced store paths
grip gc --dry-run                  # show what gc would reclaim
grip why-owns <path>                # which module owns a deployed path
grip doctor                         # check config, deno, the embedded frontend
grip trust list/add/remove          # the repo trust list — the gate before any eval
grip store verify [--repair]        # re-hash store paths against expectations
grip self-update                    # update grip itself from the latest core release
```

All shipped; the config schema on this page is their stable contract.
