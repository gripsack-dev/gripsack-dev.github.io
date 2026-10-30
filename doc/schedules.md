# Scheduled tasks

A schedule invokes a finite task through the Linux systemd user manager. There is no Gripsack daemon. A declaration, import, check or plan never registers a timer: explicit profile application owns registration.

## Prerequisites

Use the Linux x86_64 static release binary and a reachable supported systemd 255 user manager. WSL2 must have a usable systemd user session; merely being WSL2 is not enough. Check capability before applying:

```sh
grip jobs capability
```

The runner is retained with the captured registration. There is no root-service or linger fallback. Unsupported or unreachable managers fail closed. These prerequisites describe the implementation contract, not a claim that every host has been qualified.

## Register the same task you run manually

Start from the complete Bash `gripsack.ts` in [tasks](tasks.md#literal-bash-bodies). Add `daily`, `schedule` and `profile` to its imports, then add these declarations before its export:

```typescript
const nightly = schedule("nightly", { task: "greet", trigger: daily("03:30") });
const personal = profile("personal", { schedules: ["nightly"] });
```

Replace the export with:

```typescript
export default defineWorkspace(() => workspace({
  outputs: [shell, dev, greet, nightly, personal],
}));
```

```sh
grip update
grip task run greet --closed-stdin
grip plan personal
grip apply personal
grip jobs status --json
```

Review source and lock approvals, then the registration plan before applying. Daily and weekly calendar triggers use local time. This example only prints a greeting: it does not back up or mutate a database. Tasks that mutate shared resources should declare appropriate store-scoped locks so manual and scheduled invocation participate in the same conflict policy.

## Inspect, disable and remove

Use the actual job and invocation identifiers from status and receipts:

```sh
: "${job:?set the registered job ID}"
: "${invocation:?set the task invocation ID}"
grip jobs status "$job" --json
grip jobs log "$invocation"
grip jobs disable "$job"
```

Remove the schedule from the profile's selection and apply the profile to remove registration. Profile rollback restores the retained registration capture, not effects from previous task runs. Update source or pins and explicitly apply again to replace the registered capture; timers do not evaluate current TypeScript at firing time.

## Execution boundaries

Scheduled invocation uses closed stdin, bounded logs and a 1,800-second runtime limit. Timers use `Persistent=false` with native missed-event behavior, not promised catch-up delivery. Stale callbacks are refused; already-admitted old invocations may finish. Read logs as private application output. Retain independent backups and do not assume task side effects are reversible.

Tasks requiring [services](services.md) still require already-healthy services. Scheduling does not start Docker containers implicitly. The [complete captured scheduled-task example](https://github.com/gripsack-dev/gripsack/tree/{release_source}/examples/workspaces/04-scheduled-task) shows a package-command task and store lock.
