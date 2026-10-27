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


## `[capture]` — env.toml only

| key | type | default | what |
|---|---|---|---|
| `exclude` | string array | `[]` | repository-relative literal subtrees and, in 0.48, explicit bounded glob patterns omitted from capture |

Ignored and untracked files are captured unless explicitly excluded; Git ignore
files never define source authority. Exclude virtual environments with outbound
links and recurring tool caches. An editor-only SDK can be excluded literally
so evaluation uses the matching frontend embedded in the core:

```toml
[capture]
exclude = [".venv", "node_modules/@gripsack/core", "**/__pycache__", "**/.ruff_cache"]
```

Semantics:

- Literal entries are normalized repository-relative subtree names.
  Patterns add `*` within one path component, `?` for one character and
  whole-component `**` across components. Matching is case-sensitive and
  bounded; `~`, parent traversal, absolute paths, backslashes and control
  characters are not accepted path shortcuts.
- Required configuration, entrypoints and lock authority cannot be excluded.
  An admitted SDK pin is captured as a complete root: any glob that could
  filter its root or descendants refuses, even if no matching cache exists yet.
- The literal `"node_modules/@gripsack/core"` exclusion disables that runtime
  pin before it is dereferenced; it is useful for an editor-only SDK. This is
  different from a wildcard carving an admitted pin. With a symlinked
  `node_modules` parent, exclude that whole parent or use real ancestry.
- Prefix-scoped globs require real, unaliased potential ancestry. Do not span
  captured file/directory aliases with them. A leading suffix glob such as
  `**/__pycache__` avoids that restriction, provided it does not overlap an
  admitted auxiliary root. The embedded frontend is the straightforward choice
  for aliased content trees using global cache globs.
- Policy spellings are bound into the approved bundle. Changing contents,
  creating or removing glob-matched caches beneath existing directories does
  not change capture identity. Adding an ordinary parent directory does.
  Literal excluded roots retain their historical appearance/removal identity.
- Escapes and attempts to access excluded aliases name the logical path and
  fail; there is no live-tree fallback.
- `grip trust inspect` (JSON report version 2) exposes configured exclusions and
  complete inventory changes. `--focus PREFIX` narrows only the displayed
  changed paths, with an unhidden count/digest of other changes; approval still
  binds the whole bundle and policy. JSON remains complete.
- Evaluator runtime grants never overlap the repository or its
  exclusions, checked at approval and again at launch against the
  paths' original spelling before canonicalization.
- Evaluator runtimes receive **exact-file read authority**, never
  whole directories: for native evaluators, the selected executable,
  its loader/ldd-derived libraries and `/etc/ld.so.cache`; for script
  wrappers, the exact selected wrapper/interpreter/runtime files;
  selected Python stdlib/purelib directories remain explicit
  interpreter-installation data (`pyvenv.cfg` exact, no sys.prefix-wide
  grant), discovered via `python -I` in a fresh empty non-repository
  temp directory with the original interpreter/venv argv0 preserved.
  Resolved native/interpreter/engine executable digests and the exact
  file/directory grants bind `native_configuration_sha256` — an
  interpreter upgrade or PATH swap requires renewed approval — and
  `grip trust inspect` (JSON v2) exposes the resulting
  `runtime_access`.
- This is repository-source selection, not a prohibition on
  explicitly declared native host effects.
- `env.toml` itself must be a regular non-symlink file of at most
  1 MiB; a config change during capture is refused before evaluation.

See [unattended approval](safety.md#unattended-approval) for how
exclusions interact with the approval digest.

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
| `GRIPSACK_TRUST_ALL` | refused: `=1` fails with migration guidance — inspect the captured bundle and approve exact digests ([unattended approval](safety.md#unattended-approval)) |
| `SSL_CERT_FILE` | the corporate CA bundle — grip's rustls-based fetching honors it and the tools grip spawns inherit it, so TLS-intercepting proxies verify; set it before invoking grip |
| `HTTPS_PROXY` / `NO_PROXY` | corporate proxy support; the system CA roots are trusted |
| `XDG_DATA_HOME` | honored for the default `GRIPSACK_HOME` |

## CLI surface

```bash
grip init [DIR]                     # scaffold a legacy env repo from the embedded template
grip adopt <path>                   # legacy adoption interview; see migration and recovery limits
grip apply [PROFILE...]             # deploy workspace profiles; unchanged complete state can reuse its generation
grip plan [PROFILE...]              # prepare the selected workspace profile changes without deployment
grip apply --host H [MODULE...]     # retained legacy host/module workflow
grip apply PROFILE --migrate-from N # adopt intact paths from exact current legacy generation; plan first
grip check                         # validate the workspace or legacy environment
grip build OUTPUT                  # realize a named package or recipe without activation
grip run --env ENV -- COMMAND       # execute in a selected project environment
grip shell ENV                     # open its interactive shell
grip task list                     # list manual tasks
grip task plan NAME                # inspect a task invocation
grip task run NAME                 # execute prerequisites, ordered steps and checks
grip task status INVOCATION_ID      # inspect retained invocation status
grip task log INVOCATION_ID         # read its retained output
grip update [NAME...]               # refresh source and frontend/import pins without deployment
grip update --check [NAME...]       # survey only; 0 current, 1 changes, 2 incomplete/error
grip rollback [N]                   # restore a retained generation
grip generations                   # list retained generations
grip gc [--dry-run]                 # collect or inspect unreferenced store paths
grip why-owns PATH                 # inspect managed destination ownership
grip doctor                        # inspect runtime/frontend selection
grip trust inspect [--focus PREFIX] --json
grip trust add                     # review and approve the exact current source/policy
grip trust list
grip trust remove
grip hooks list                    # inspect durable hook outcomes without running hooks
grip store-verify [--repair]        # verify store content
grip self-update                   # verified signed-release path; not an unsigned-release installer
```

`update` completes source pins in one lockfile write. Source-only merged
artifacts become an unrooted cache: GC may evict them before the first apply,
and a pinned cold apply reconstructs them without another lockfile change.
Retained generations continue to protect their artifact roots. Build recipes
and hooks are never executed by update.

`update --check` performs resolution and acquisition in private scratch without
publishing source-cache artifacts or writing the lockfile. It reports per-module
failures without hiding the rest of the survey. Exit **0** means complete/current;
**1** means complete with changes; **2** means incomplete or an operational error.
The command can use the network; normal eval/runtime provisioning and run-log
bookkeeping still apply. It neither deploys nor runs recipes/hooks/verifiers.
Known source-only layout errors fail before publication; unavailable artifacts
and recipe-produced paths are explicitly deferred.

Self-update holds a per-executable lock and rechecks the installed version,
so an older waiting updater cannot downgrade it. Publication checks mode,
syncs bytes, renames, then syncs the directory. An error after rename reports
that the executable changed; it never attempts an automatic rollback.

These are supported command families; use `grip COMMAND --help` for their
selection and safety options. This page does not promise registry publication
or change the signature requirements of the existing updater.
