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

## `[eval]` — env.toml only

| key | type | default | what |
|---|---|---|---|
| `deps` | string[] | `[]` | frontend-environment packages the modules import at eval time (resolvers, sourcerer libraries). Pinned; content-cached |

## `[sources.<name>]` — env.toml or user config

| key | type | default | what |
|---|---|---|---|
| `plugin` | string | — | sourcerer executable for this source; default discovery is `gripsource-<name>` on `PATH` |

Repo entries override user entries of the same name.

## `[settings]` — env.toml or user config

| key | type | default | what |
|---|---|---|---|
| `keep_generations` | integer | ∞ | generations retained before `grip gc` reclaims store paths |

## Environment variables

| var | what |
|---|---|
| `GRIPSACK_HOME` | base directory for store, generations, and the `current` symlink (default: `$XDG_DATA_HOME/gripsack` or `~/.local/share/gripsack`) |
| `GRIPSACK_BIN` | path to the `grip` binary (used by the e2e harness) |
| `XDG_DATA_HOME` | honored for the default `GRIPSACK_HOME` |

## CLI surface

```
grip apply [--host H] [MODULE...]   # fetch, build, deploy — one new generation
grip plan [--host H] [MODULE...]    # show what apply would change
grip rollback [N]                   # flip current back to generation N
grip generations                    # list generations and their status
grip gc                             # collect unreferenced store paths
grip why-owns <path>                # which module owns a deployed path
grip doctor                         # check config, runtime, frontend env
```

Subcommands other than `doctor` are being implemented; the config
schema on this page is their stable contract.
