# Architecture

Gripsack separates declarations, production, execution and personal deployment. A workspace is the shared graph; each operation takes only the authority needed for its stage.

## From source to declared graph

1. **Capture:** the core snapshots repository inputs under an explicit capture policy.
2. **Approve:** the operator reviews the exact source bundle and policy identities.
3. **Evaluate:** the matching TypeScript frontend runs in provisioned Deno with restricted reads and no ambient network, environment or subprocess access.
4. **Admit:** the Rust core validates the resulting intermediate representation, references, dependency graph and execution contracts.

The public authoring surface is `gripsack.ts` and `@gripsack/core`. The intermediate representation is an implementation contract, not a second hand-maintained configuration language. Use matching core and frontend bytes rather than assuming a wire version grants another implementation's authority.

## Sources and packages

Providers acquire immutable source inputs and package closures. Native Conda solves a coherent environment; explicit Pixi imports consume a captured manifest/lock selection. `gripsack.lock` binds platform-keyed source and frontend/import identities. `grip update` refreshes those records without deploying files.

A package gives a native provider's output a target, layout, commands and runtime dependencies. Packages can be selected into environments, profiles and tasks without duplicating source resolution policy. See [packages](packages.md) and [sources](fetchers.md).

## Services and transport

[Services](services.md) declare digest-pinned Docker Engine containers, named volumes, loopback ports and readiness checks. Startup is explicit; Gripsack does not run a daemon. Service data is outside profile generations.

[Native artifact sharing](sharing.md) moves retained native closures. Its OCI registry transport is not a container image builder or runtime. The previous [source builder](builds.md) has been retired.

## Native execution

An environment selects compatible packages and explicit command exports. Native invocation admits the selected runtime closure instead of treating arbitrary `PATH` or ambient loader search as authority. Host-runtime dependencies are explicit opt-ins and remain mutable host inputs, not portable image content.

Tasks add command graphs, prerequisites, declared mutation locks and postconditions. Their receipts describe invocation outcomes. [Scheduling](schedules.md) requires explicit registration with the user service manager; declaring a schedule does not register a timer.

## Personal deployment

Profiles combine captured files, retained artifacts and selected environment launchers. Apply realizes required packages before changing destinations, then uses journaled ownership transitions and an atomic generation-selection flip. Destination writes are not atomic across the entire profile.

Retained generations preserve package roots, file content, launcher bindings and recovery information. Rollback reuses retained bytes rather than re-running today's source or build. Local tracked-copy drift remains protected. Hooks and explicit native commands can have effects outside managed files; those are not whole-machine transactions.

See [profiles](adopting.md) and [safety](safety.md) for exact ownership and recovery boundaries.

## Where the implementation lives

The [core source](https://github.com/gripsack-dev/gripsack/tree/{release_source}/crates), [TypeScript SDK](https://github.com/gripsack-dev/gripsack/tree/{release_source}/typescript) and [technical guarantee ledger](https://github.com/gripsack-dev/gripsack/blob/{release_source}/verification/guarantees.md) hold implementation contracts and evidence. Product examples use public authoring declarations, not historical internal envelopes.
