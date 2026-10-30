# Settings reference

Operational settings for workspaces. See [settings](settings.md) for source capture and frontend selection, and `grip COMMAND --help` for the installed CLI's complete options.

## Files and precedence

| Layer | File | Typical ownership |
|---|---|---|
| User | `~/.config/gripsack/config.toml` | Local operator defaults |
| Repository | `env.toml` | Reviewed workspace policy |

Precedence, later wins: built-in defaults, user configuration, repository configuration, environment variables, CLI flags. Settings are read before workspace evaluation. A file-only workspace does not require `env.toml`.

## Source capture

Repository `env.toml`:

```toml
[capture]
exclude = [".venv", "node_modules/@gripsack/core", "**/__pycache__"]
```

`exclude` is a string array, defaulting to `[]`. Entries are normalized repository-relative literal subtrees or bounded glob patterns. Required inputs and admitted SDK roots are protected. The literal SDK exclusion explicitly selects the embedded frontend; glob exclusions cannot partially filter an admitted pin. See [capture policy](settings.md#source-capture).

## Execution environment

Repository `[eval].env` is a string map, defaulting to `{}`. It supplies environment values to the operation's execution process; the sandboxed TypeScript evaluator does not receive ambient environment access. Supply credentials through trusted operator configuration, not committed secrets.

## Acquisition and retention

`[settings]` is supported in repository and user configuration:

| Key | Default | Meaning |
|---|---|---|
| `keep_generations` | Unlimited | Retained generations before garbage collection can reclaim unreferenced content |
| `acquisition_jobs` | `2` | Maximum simultaneous payload acquisitions |
| `download_limit_bytes` | `536870912` | Download cap per payload, 512 MiB |
| `expanded_limit_bytes` | `4294967296` | Expanded stream/tree cap, 4 GiB |
| `archive_entry_limit` | `100000` | Archive/materialized-tree entry cap |
| `decoder_memory_bytes` | `134217728` | Decoder working-memory/window budget, 128 MiB |

Acquisition values are positive integers; zero is not unlimited. Repository values override user defaults. Limits fail closed without partial publication. Retention does not allow GC to remove the current generation or content protected by retained generations and recovery roots.

## Rate budgets

Repository `[throttle]` assigns budgets per API domain:

```toml
[throttle]
"api.github.com" = "30/min"
```

Units are `s`, `min` and `hr`. Bucket state persists in the private state root so successive operations share the budget. Local pacing does not override upstream quota. Release CDN downloads do not inherit an API domain's bucket.

## Environment variables

| Variable | Purpose |
|---|---|
| `GRIPSACK_HOME` | Private store, generations, trust and recovery state root |
| `XDG_DATA_HOME` | Parent of the default state root when set |
| `GRIPSACK_DENO` | Deliberately selected evaluation runtime |
| `GRIPSACK_LOG` | Console log filter; JSONL retains its own threshold |
| `SSL_CERT_FILE` | Corporate CA bundle for native fetching |
| `HTTPS_PROXY`, `NO_PROXY` | Network proxy policy |
| `GITHUB_TOKEN`, `GH_TOKEN` | Public GitHub credentials, in that precedence |
| `GITHUB_ENTERPRISE_TOKEN`, `GH_ENTERPRISE_TOKEN` | Enterprise credentials, requiring a matching `GH_HOST` or `GITHUB_HOST` |

`GRIPSACK_TRUST_ALL=1` is refused. Use exact-digest [source approval](safety.md#unattended-approval), not a floating trust setting.

## Command map

```sh
grip check                         # validate workspace declarations
grip plan [PROFILE...]             # prepare selected profile changes
grip apply [PROFILE...]            # deploy selected profiles
grip build OUTPUT --json           # realize a native package output
grip run --env ENV -- COMMAND       # run in a selected environment
grip shell ENV                     # open its interactive shell
grip task list                     # list manual tasks
grip task plan NAME                # inspect one invocation graph
grip task run NAME                 # run prerequisites, steps and checks
grip task status INVOCATION_ID      # read retained status
grip task log INVOCATION_ID         # read retained output
grip update                        # refresh source/frontend/import pins
grip update --check                # survey without lock/source publication
grip generations                   # list retained generations
grip rollback [N]                  # restore a retained generation
grip gc --dry-run                  # preview native reclamation
grip why-owns PATH                 # inspect destination ownership
grip doctor                        # inspect runtime/frontend selection
grip trust inspect --json          # inspect captured source and policy
grip trust add                     # review and approve exact current inputs
grip trust list
grip trust remove
grip hooks list                    # inspect durable hook outcomes
grip store-verify                  # verify retained store content
grip up [SERVICE...]               # start services and await readiness
grip down [SERVICE...]             # remove owned containers, retain volumes
grip services status --json        # inspect recorded service state
grip services logs SERVICE         # read bounded container output
grip jobs capability               # inspect user-manager prerequisites
grip jobs status --json            # inspect registered scheduled tasks
grip snapshot current --out FILE   # save a private semantic snapshot
grip diff BEFORE AFTER --json      # compare captured semantic states
grip plan PROFILE --save FILE      # save exact deployment bindings
grip apply --saved-plan FILE       # apply only if bindings remain valid
grip package --help               # passive native artifact sharing
```

`update --check` returns 0 for complete/current, 1 for complete/changes and 2 for incomplete/error. It can use the network and initialize runtime/log state, but it does not deploy or execute hooks. `plan` is not an apply: follow [ownership guidance](adopting.md) before authorizing destination changes.

## Recovery and diagnostics

Keep generation manifests and journals rather than treating them as caches. Use [run logs](runs.md) to investigate, [safety](safety.md) to understand recovery boundaries, and the [SDK reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) for declaration contracts.
