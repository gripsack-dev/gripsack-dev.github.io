# How it works

One binary, `grip`, with the TypeScript frontend embedded. It evaluates your workspace in a sandbox, turns the result into a typed intermediate representation, and executes that against a content-addressed store with generations. This page follows one declaration from file to deployed state and names the parts along the way.

## From `gripsack.ts` to a plan

1. **Capture.** The core snapshots the repository (minus explicit [exclusions](settings.md#source-capture)). Git ignore rules are not a policy; everything in the tree is part of what you approve.
2. **Approve.** You review and approve the exact bundle and policy digests ([source approval](safety.md#source-approval)).
3. **Evaluate.** A pinned, checksum-verified Deno runs the embedded frontend over the captured source with no environment, network or subprocess access. Host facts arrive as inputs; anything that needs to look at the machine is an explicit probe.
4. **Admit.** The Rust core validates the resulting IR: references, dependency graph, command contracts, provenance for every declaration.
5. **Plan.** The core compares the desired state with what is live and prints exactly what would change.

The public authoring surface is `gripsack.ts` and `@gripsack/core`. The IR is an internal contract; you never write it by hand.

## Sources, packages and the store

Sources (`githubRelease`, `tarball`, `git`, `conda.environment`, `pixi.fromLock`, …) describe where bytes come from. `grip update` resolves them and records platform-keyed pins in `gripsack.lock`; that lockfile is the only source of versions at apply time. Downloads are hashed into private spools, verified, bounded, extracted and sealed read-only in the store before they get a final name.

A **package** gives a source a target platform, a layout, commands and runtime dependencies. **Environments**, **profiles** and **tasks** all select the same package declarations. Invocation re-admits the package's runtime closure each time rather than trusting whatever is on `PATH`.

## Deployment and generations

A **profile** combines files, retained package artifacts and launchers for one environment. `grip apply` realizes packages first, then runs the [transaction](safety.md#what-apply-does): journal, write with ownership checks, pre-flip checks, one atomic flip of `current`, hooks. Every applied state is a **generation** that keeps its package roots, file content, launcher bindings and recovery data, so `grip rollback` reuses bytes instead of re-running today's source.

## Services, tasks and schedules

[Services](services.md) are digest-pinned containers driven through the Docker Engine API; gripsack owns only the containers and volumes it created and never runs a daemon. [Tasks](tasks.md) are command graphs with prerequisites, locks and postconditions; [schedules](schedules.md) register those tasks with the systemd user manager during profile application. [Sharing](sharing.md) moves signed, passive package bundles between machines or through an OCI registry without evaluating anything on the receiving side.

## The rings

The code is arranged so that the decisions that matter most are smallest and best checked:

| Ring | Crates | Checked by |
|---|---|---|
| Kernel | `gripsack-kernel` | Lean 4 proofs over the shipped Rust |
| Protocol | transaction machines in `gripsack-store`, `gripsack-exec` | crash-injection tests, TLA+ model; Lean proofs next |
| Host | `gripsack-fs`, `gripsack-process`, store layout | small, every assumption listed, fault injection |
| Edge | `gripsack-ir`, `gripsack-fetch`, `gripsack-conda`, services, schedules | sandbox, typed admission, hash-verified bytes, fuzzing |
| Product | `gripsack` (the CLI) | end-to-end flows |

[How gripsack stays safe](guarantees.md) spells out what each ring guarantees and what it does not.

## Where the implementation lives

The [core crates](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates), the [TypeScript SDK](https://github.com/gripsack-dev/gripsack/tree/{release_source}/typescript), the [proofs](https://github.com/gripsack-dev/gripsack/tree/{release_source}/proofs) and the [design records](https://github.com/gripsack-dev/gripsack/tree/{release_source}/plan) are all in one repository.
