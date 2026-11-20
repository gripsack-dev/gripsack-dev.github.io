# What's new

User-visible changes per release. The [full changelog](https://github.com/gripsack-dev/gripsack/blob/{release_source}/CHANGELOG.md) and [release downloads](https://github.com/gripsack-dev/gripsack/releases) live with the source. This site documents core **{core_version}**.

## 0.56.0 — Typed artifact selectors and live task output

- Typed `artifact(output, selector)` references now expand locked version and platform tokens in exec arguments, command env/cwd and environment env, consistently across tasks, checks, hooks and scheduled commands. Package-subject `sourcePath` selectors use the subject's locked version.
- Every reference uses its own package's frozen source, with exact raw-tag or one-lowercase-`v` bare spelling. Literal arguments, environment values, working-directory paths and scripts remain literal.
- Plans include these selectors in text and JSON `resolved_paths`, without fetching or promising existence. Missing versions, unknown tokens and unsafe expanded paths fail with declaration provenance; canonical containment applies to cwd too.
- Retained hooks, launchers and portable bindings keep concrete selectors, and historical literal portable selectors are not reinterpreted. Attached file checks still allow only `sourcePath(".")`.
- Ordinary `grip task run` labels dependency steps and postcondition checks as they start and finish, and flushes stdout chunks immediately, including partial lines. Stdout remains unchanged for pipelines; progress uses stderr. Child stderr is captured per process and printed on completion; `--json` stays capture-only.
- Apply's live progress and separate check/hook blocks were already present in 0.54; verification output is captured per check/hook, not buffered across the whole apply.

## 0.55.0 — Locked-release payload paths

- Package command values, `artifactFile` selectors and `artifactTree` include/exclude segment prefixes accept the same version and platform tokens as GitHub release assets.
- Payload paths bind to the referenced package's resolved/locked source; lock-only updates can move commands and file/tree consumers without editing declarations. Raw tags are preserved, and `{version.bare}` strips exactly one leading lowercase `v`.
- Plans show expanded paths before package or artifact realization without fetching payloads; JSON plans include `resolved_paths`. Missing required versions, unsupported tokens and unsafe expanded relative paths fail with declaration provenance.
- Command/environment `artifact` selectors and package-check `sourcePath` selectors did not expand in this release; that gap is addressed in 0.56.0.

## 0.54.0 — The whole apply, proved

- Changing only the case of a file name on a case-insensitive filesystem (WSL's `/mnt/c`, macOS) no longer deletes the file during `apply` or `rollback`; two spellings that resolve to the same object are one destination.
- Each post-activation hook now re-checks the selected generation before launch; if an earlier hook switched generations, the remaining hooks in the batch do not run.
- `grip apply` streams progress as it works, and each check or hook prints one separated block with its output under a gutter and a pass/fail line; `--verbose` shows passing output in full. Piped and `NO_COLOR` output has no colour codes.
- `apply` and `rollback` re-check each destination just before writing it and refuse a change they detect. An outside write can still race the operation after that re-check.
- Release-archive targets no longer need `abi`: it is read from the executable. Conda environments use conda-forge's host platform libraries (X11, GL, ALSA) as conda-forge expects; `strict: true` refuses them.
- The release gate exercises the complete workspace examples in these docs. Conda, Pixi and Docker examples are evaluated, checked and planned, not applied by that gate.
- `grip apply`, managed blocks, garbage collection, the journal run, activation and `grip update`'s lock decision now run from `gripsack-kernel` and are proved in Lean: 579 theorems. See [how gripsack stays safe](guarantees.md).

## 0.53.0 — Proved ownership and rollback

- `rollback` restores exactly what the target generation recorded (bytes and mode, or link target), from bytes gripsack retained, or refuses before switching. It used to guess a missing mode, re-render old templates, skip a destination it could not restore and still switch, and write a shell profile into a pre-0.22 generation; all four are fixed.
- `apply` no longer re-points a gripsack-managed symlink you replaced with your own file; it stops and names it, and `--take-over` absorbs it. A link you made into gripsack's store is no longer treated as gripsack's.
- `install.sh` and `grip self-update` work again: they verify the published SHA-256 and install atomically, with no GitHub CLI, Python or signed manifest.
- Crash recovery refuses by name, instead of wedging, when a destination became a directory, FIFO, socket or device; `grip doctor` shows the pending journal.
- The recover machine, the per-file ownership decision and the rollback machine now run from `gripsack-kernel` and are proved in Lean: 157 theorems. See [how gripsack stays safe](guarantees.md).

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
