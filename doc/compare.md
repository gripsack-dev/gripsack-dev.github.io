# Compare

How gripsack sits next to the tools you already know. It does not
replace an OS package manager — brew or apt keep handling binaries —
it manages user-space tools and your configuration, one file at a
time, with generations and rollback. The honest row-by-row:

| | gripsack | nix + home-manager | chezmoi | stow | apt · brew · mise |
|---|---|---|---|---|---|
| adopts the machine you already have | ✓ one file at a time | rebuild from config | whole files | symlinks only | · |
| manages mutable, shared configs | ✓ merge blocks + drift detection | whole files only | templates + modify_ scripts | · | · |
| rolls the managed environment back | ✓ generations | ✓ | git history | · | · |
| packages and dotfiles in one repo | ✓ | ✓ | packages via run_ scripts | · | tools/env/tasks; dotfiles via bootstrap |
| reproducible inputs | lockfile pins (sha-verified) | ✓ stronger: sandboxed builds | ✓ | · | · |
| no daemon, no root, no takeover | ✓ | /nix store (single-user no-daemon install exists) | ✓ | ✓ | apt needs root |
| config language | typed TypeScript API | nix lang | templates | · | · |

Fair is the point: Nix is the stronger guarantee. gripsack borrows one
of its best ideas — generations — and stays a tool you can adopt [one
dotfile at a time](adopting.md).
