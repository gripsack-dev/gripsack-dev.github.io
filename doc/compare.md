# Where gripsack fits

Gripsack manages user-space tools, project environments and personal configuration. It is not an operating-system package manager. Keep apt or another system manager for the OS; select the packages and files you want in a workspace.

## Choose the scope you need

| Tool | Typical focus | Why choose it |
|---|---|---|
| gripsack | Typed native packages, environments, personal profiles, tasks and Docker Engine services | One workspace graph with explicit source review, file ownership and retained generations |
| Nix + Home Manager | Declarative package graphs and home configuration in the Nix ecosystem | Broad package ecosystem and established derivation/configuration workflows |
| chezmoi | Personal configuration source state and templates | Focused dotfile management with rich templating |
| GNU Stow | Symlink trees | Small, direct link management without a package producer graph |
| apt / other OS managers | Distribution packages and system integration | Operating-system dependency and installation policy |
| mise | Developer tool versions, environments and tasks | Its tool ecosystem and project task workflow |

These are scope comparisons, not a claim that other tools cannot be extended or combined.

## When gripsack is useful

- You want tools from release archives, captured source or a coherent Conda solve without global user-space installs.
- You want a project environment and a personal command launcher to select the same packages.
- You want an explicit, digest-pinned local database alongside native project tools.
- You want copied configuration with drift guards, store-owned links or small managed blocks rather than one ownership policy for every file.
- You want manual tasks and lifecycle checks to be named, inspectable outputs.

Start with a [file-only workspace](workspaces.md), a [native package](packages.md) or [PostgreSQL service](services.md).

## Deliberate boundaries

Current host support is Linux x86_64 and WSL2. Container services need Docker Engine; native file profiles do not. Scheduled tasks require explicit profile application and a supported user service manager. Native artifact sharing is not automatic registry deployment or container-image building.

Generations and journals protect managed state, not every effect on the machine. Tracked-copy drift is preserved by default; arbitrary tasks, services and hooks are not automatically reversible. Alpha software still needs independent backups and actual consumer checks. See [safety and recovery](safety.md) and [installation](install.md).
