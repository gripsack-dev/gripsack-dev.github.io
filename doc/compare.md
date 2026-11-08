# Where gripsack fits

Gripsack manages the user-space layer: tools, project environments, personal configuration and the project services next to them. It is not an operating-system package manager. Keep apt or your distribution for the OS and put the pieces you want reviewed and reversible in a workspace.

## Next to other tools

| Tool | Focus | Compared with gripsack |
|---|---|---|
| Nix + Home Manager | Declarative packages and home configuration in the Nix ecosystem | Much larger package ecosystem and its own language. Gripsack is one static binary, TypeScript, and takes packages from upstream archives and Conda instead of a derivation set |
| chezmoi | Dotfiles with templates | Deeper templating. Gripsack adds per-file ownership modes, drift detection, generations and rollback, and manages tools and services with the same file |
| GNU Stow | Symlink farms | Smaller and simpler. Gripsack's `symlinkTo` is the equivalent; tracked copies and managed blocks cover files that symlinks cannot |
| mise | Developer tool versions and tasks | Focused on language runtimes. Gripsack pins arbitrary archives and Conda solves, deploys launchers through generations, and adds services and schedules |
| apt / dnf / pacman | Distribution packages | The OS layer. Gripsack deliberately stays out of it |

These are scope comparisons; the tools combine fine.

## When it is a good fit

- You want tools from release archives or a coherent Conda solve without installing into a global prefix, and the same tools for project commands and personal launchers.
- You want dotfiles deployed with a plan you can read first, your local edits preserved, and a one-command way back.
- You want a project database pinned by digest on a loopback port, next to the native tools, without running a daemon.
- You want named tasks, pre-deployment checks and calendar schedules to be declarations you can review rather than scripts you remember.
- You care whether the safety claims are checked. The [core decisions are proved](guarantees.md), and the page says what is not.

## Boundaries

Linux x86_64 and WSL2 only. Container services need Docker Engine; schedules need a systemd user session; file-only profiles need neither. Generations protect managed files and launchers, not database contents, task effects or hook side effects. Alpha software: keep independent backups. See [safety and recovery](safety.md) and [installation](install.md).
