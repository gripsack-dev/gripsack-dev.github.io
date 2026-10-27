# Compare

Gripsack 0.48 manages user-space packages, environments and configuration,
not the operating system. New authoring uses a root `gripsack.ts` workspace;
legacy host/module repositories remain supported. You can leave system
packages with apt or another manager and adopt only the files you choose.

| | gripsack 0.48 | Nix + Home Manager | chezmoi | GNU Stow | apt / Homebrew / mise |
|---|---|---|---|---|---|
| primary scope | user packages, environments and profiles | declarative packages and home configuration | dotfiles | symlink trees | system packages / packages / developer tools and tasks |
| existing files | explicit takeover with prior-state capture | declarative activation; conflicts need a migration policy | import files into source state | link conflicts need resolution | not a shared dotfile ownership model |
| mutable or shared config | tracked copies with drift guards; managed text blocks | managed files, with application-specific escape hatches | templates and modification scripts | no content reconciliation | tool-specific |
| rollback | retained generations and journaled file ownership | generations for managed configuration/packages | source history and re-application | relink another tree manually | manager- and package-specific |
| pinned inputs | captured source, platform locks and verified archive identities | dependency graph and sandboxed builds, subject to derivation policy | source-controlled config; external tools need separate pinning | source tree only | manager-specific locks and checksums |
| authoring | typed TypeScript, evaluated in a sandbox | Nix language | templates and scripts | directory layout | package manifests and tool-specific configuration |

These are scope comparisons, not claims that another tool cannot be extended.
Nix is the stronger general-purpose reproducible-build system. Gripsack's
captured inputs and lockfiles do not make legacy shell steps hermetic or
undo arbitrary external effects. Workspace recipes use an explicit production
contract; the qualified owned-worker route is Linux x86_64 with Docker, not
an unconditional “no daemon” promise.

Gripsack's supported hosts are **Linux and WSL2 on x86_64**, not macOS or
native Windows. File-only profiles need no build worker; provider-backed
packages and retained outputs can also avoid a worker. A file-only adoption
can be incremental, but taking ownership still requires a deliberate decision.
Rollback requires retained history and respects drift; late activation failure
is not an automatic whole-machine undo. See [adoption](adopting.md),
[workspace migration](workspace-migration.md), and [safety](safety.md).

## Release status

[Core 0.48](https://github.com/gripsack-dev/gripsack/releases/tag/core-v0.48.0)
is the public latest release, **unsigned**, with 17 practical local gates
and 96 persistence partitions passed. TLC, TLAPS and Verus remain explicitly
unqualified; these results are not formal qualification or completion of the
original roadmap. Core 0.47 remains an unsigned, unverified prerelease.

Use the release's manual archive installation instructions: 0.48 has no npm
or crates.io publication, and the signed core installer/updater still fails
closed. The documentation website is built locally and does not require
signed release artifacts; its availability is not release-authentication evidence.
