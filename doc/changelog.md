# What's new

User-visible changes per release. The [full changelog](https://github.com/gripsack-dev/gripsack/blob/{release_source}/CHANGELOG.md) and [release downloads](https://github.com/gripsack-dev/gripsack/releases) live with the source. This site documents core **{core_version}**.

## 0.52.0 — Verified foundation, phase one

A foundation release: no command or workspace authoring changes.

- Commit classification after a crash, garbage-collection admission and pruning, and journal record publication now run from `gripsack-kernel`, a dependency-free crate whose Rust is translated to Lean 4 and proved there: 34 theorems, standard axioms only, each calibrated against deliberately broken variants. Behaviour is unchanged; the proofs cover the exact code that ships. See [how gripsack stays safe](guarantees.md).
- Release assets no longer include the release-evidence JSON, runtime-evidence JSON or qualification bundle. The core tarball, Conda helper, SDK tarball, checksums and `install.sh` are unchanged in form.
- Internally, a release is now local qualification of the exact source plus one script that publishes the same bytes. The committed evidence logs and receipt checkers are gone.

## 0.51.0 — Native workspaces

- Literal `bash` template blocks with a pinned interpreter, typed environment bindings and strict shell options; JavaScript interpolation into shell text is rejected. See [tasks](tasks.md#literal-bash-bodies).
- [Docker Engine services](services.md): digest-pinned images, loopback ports, retained named volumes, health commands and dependency ordering. Tasks can require healthy services without starting them.
- [Scheduled tasks](schedules.md) on systemd user managers, registered by profile application and sharing the manual task runner, locks and logs.
- [Offline semantic review](review.md): snapshots, generation diffs, configuration views and private saved plans that refuse to apply when their bindings go stale.
- [Signed package bundles](sharing.md) with complete dependency closures and OCI registry transport; recipients select imported content from their own workspace.
- Conda reconstruction from original archives and explicitly hash-pinned wheels, including wheel records from an imported Pixi lock.
- Removed: macOS/Homebrew authoring and the BuildKit source-build and image backend.

## 0.50.0 — One workspace

- One authoring surface: `gripsack.ts` describes packages, environments, profiles, tasks and more, through `@gripsack/core`.
- `grip init` scaffolds a workspace; `grip adopt` brings an existing configuration directory into one.
- Removed the legacy module DSL and macOS/Lima backends. Linux x86_64 and WSL2 is the target.
- `store-verify` audits retained native packages and environments.
