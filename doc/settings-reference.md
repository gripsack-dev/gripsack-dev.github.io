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
| `frontend` | `"python"` \| `"typescript"` | `"python"` | which frontend evaluates this repo |
| `default_host` | string | — | the host entrypoint when no `--host` is given and the machine's hostname matches nothing in `hosts/` — role-named host files for ephemeral containers with random hostnames. An unmatched host with a non-empty `hosts/` is an error, not silently-empty tags |

## `[eval]` — env.toml only

| key | type | default | what |
|---|---|---|---|
| `deps` | string[] | `[]` | frontend-environment packages the modules import at eval time (resolvers, fetcher libraries). Pinned; content-cached |

## `[fetchers.<name>]` — env.toml or user config

| key | type | default | what |
|---|---|---|---|
| `plugin` | string | — | fetcher plugin for this source; default discovery is `gripfetch-<name>` on `PATH` |

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
| `GRIPSACK_PYTHON` | bring-your-own interpreter: skip eval provisioning (provisioned plugins are then absent) |
| `GRIPSACK_EXTRA_INDEX` | extra package indexes for eval/plugin provisioning, comma-separated — e.g. `https://gripsack.dev/simple` (the `griplint-*` ecosystem index, mirrored at `https://gripsack.dev/packages`). Opt-in, not a default: it requires an egress that can reach `gripsack.dev`, which "reaches PyPI" does not guarantee — content-filtering proxies have been observed 403ing `/simple/*` while allowing the bare domain. PyPI remains the primary index everywhere |
| `HTTPS_PROXY` / `NO_PROXY` | corporate proxy support; the system CA roots are trusted |
| `XDG_DATA_HOME` | honored for the default `GRIPSACK_HOME` |

## CLI surface

```bash
grip init [DIR]                     # scaffold an env repo from the embedded template
grip apply [--host H] [MODULE...]   # fetch, build, deploy — one new generation
grip plan [--host H] [MODULE...]    # show what apply would change
grip check                         # eval + sema + linters; exit code = validity
grip update [MODULE]               # re-resolve pins into the lockfile
grip rollback [N]                   # flip current back to generation N
grip generations                    # list generations and their status
grip gc                             # collect unreferenced store paths
grip gc --dry-run                  # show what gc would reclaim
grip why-owns <path>                # which module owns a deployed path
grip doctor                         # check config, runtime, frontend env
```

All shipped; the config schema on this page is their stable contract.
