# Roadmap

Gripsack is an owner-driven environment manager: readable declarations, useful
commands and recoverable changes take priority over release-process machinery.
The detailed design and historical decisions live in the
[core plans](https://github.com/gripsack-dev/gripsack/tree/main/plan), not in a
second feature-history copy here.

## Supported platforms

**Linux and WSL2's Linux environment on x86_64.** Native Windows, macOS and ARM
are outside the active support scope. The core and internal Conda helper are
musl-static; the provisioned Deno evaluator needs a glibc Linux environment.
A working installation on one host does not qualify every GNU package or
private deployment host.

## Release qualification

[0.48.0](https://github.com/gripsack-dev/gripsack/releases/tag/core-v0.48.0)
passed the owner-approved **17-gate practical local profile**, including all
**96 Linux persistence partitions**, installed consumers, dependency audits,
reproducibility and source packaging. Builds and qualification run locally.
The release is **unsigned**; TLC, TLAPS and Verus remain separate research and
are not claimed qualified by this release. Process-fault testing is not
hardware power-loss qualification.

Use the release's manual installation instructions and matching SDK archive,
or use the frontend embedded in the core. npm/crates.io publication is a
separate event and is not implied by a GitHub release. The existing verified
installer and `grip self-update` require signatures, so they are not the path
for these unsigned assets; their checks have not been disabled.

This website has **no signature admission requirement**. It renders locally
from the site source and a selected core Git commit. A publish-only Pages job
uploads those static files; it does not compile, qualify or sign the product.
Maintainer commands are documented in
[website/build.py](https://github.com/gripsack-dev/gripsack-dev.github.io/blob/main/website/build.py).

## Reviewer prerelease and development

[0.47.0](https://github.com/gripsack-dev/gripsack/releases/tag/core-v0.47.0) remains
an explicitly unverified reviewer prerelease. Its notes disclose the Zstd
advisories issued after publication. 0.48 updates those decoder dependencies
and completes practical local qualification; neither release claims a signature.

0.48 adds recursive capture exclusions and focused changed-path review.
Capture rules still protect required inputs and admitted SDK roots. For aliased
content trees, the embedded frontend and suffix globs are the straightforward
combination; an editor-only SDK can be explicitly excluded from runtime capture.
See [capture settings](settings/reference.md#capture-envtoml-only) for the exact
pin, alias and cache-identity boundaries.

## Shipped

- **Workspaces:** named packages, recipes, environments, profiles and manual
  tasks. Linux recipes/images use BuildKit; acquisition, native execution,
  source capture, the store and activation remain native.
  [Environments and commands](environments.md).
- **Readable profiles:** captured `repoTree`, executable `templateFile`, managed
  launchers and stable archive-root selection replace common repository-owned
  generators and wrappers. [Migration guide](workspace-migration.md).
- **Ownership and recovery:** tracked copies preserve local drift; generations,
  explicit migration and rollback retain recovery boundaries.
  [Safety](safety.md) and [adoption](adopting.md).

The complete API reference is the
[0.48 SDK guide](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md).
Release-by-release history is in the [changelog](changelog.md).

## Next

- Keep the local build/release loop practical and address measured reviewer
  failures. A new signer or remote verifier is not a prerequisite for iteration.
- Finish the original handover's remaining product and evidence obligations,
  including schedule/job lifecycle, semantic comparison/saved-plan execution and
  trusted portable-artifact sharing. Shipping workspaces does not close every
  original milestone; the
  [handover ledger](https://github.com/gripsack-dev/gripsack/blob/main/plan/0054-workspace-ergonomics-and-handover-completion.md)
  distinguishes implemented behavior, pending proof and missing capabilities.
- Locked mutable overlays are not implemented. The supported workflow is a
  tracked copy followed by deliberate re-capture into reviewed repository
  source, not making the store writable or silently locking live mutations.

## North star

Installing a tool, its configuration and a usable command should remain a
small declaration with explicit source and runtime authority. Failures should
name the cause and a recovery path, without requiring every dotfiles repository
to maintain its own traversal engine, template copies or launcher framework.
