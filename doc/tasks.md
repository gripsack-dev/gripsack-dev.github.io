# Tasks and checks

Tasks make deliberate commands discoverable. Checks give validation an explicit subject and lifecycle stage. Neither is an implicit background scheduler.

## Manual tasks

Extend the [ripgrep workspace](packages.md#a-release-archive) with a named action. Add `exec`, `lit`, `packageCommand` and `task` to its imports, declare this output, and include `searchVersion` alongside `ripgrep` and `search` in `workspace.outputs`:

```typescript
const searchVersion = task("search-version", {
  environment: "search",
  steps: [
    exec({ argv: [packageCommand("ripgrep", "rg"), lit("--version")] }),
  ],
});
```

```sh
grip task list
grip task plan search-version
grip task run search-version --closed-stdin
```

`list` and `plan` inspect declarations without realizing packages or executing postconditions. `run` creates a fresh invocation, not a cached task success. Use the invocation ID returned by the command:

```sh
: "${invocation:?set this to the invocation ID returned by task run}"
grip task status "$invocation"
grip task log "$invocation"
```

Status reads the durable receipt; log reads bounded private stdout/stderr output. Review logs for private information before sharing them.

## Dependencies and mutation

`deps` names unordered prerequisite tasks that must succeed in the same invocation. A task's `steps` are ordered locally; `checks` are its invocation postconditions. Declare live mutation paths with `context: { kind: "host", mutable_paths: [...] }` and shared mutation keys with `locks: [lock("user", "editor-config")]` or store-scoped locks.

Locks coordinate declared effects; they do not grant execution authority or infer dependencies from shell text. `--skip-busy` can skip an active conflict, not bypass an unknown interrupted owner. `--timeout-seconds` bounds realization, prerequisites and verification together. Interrupted or indeterminate outcomes are not recorded as success.

Use typed `packageCommand`, `lit` and explicit `env`/`argv` values for commands. A `runBash` body requires a declared package-command interpreter; it does not discover ambient Bash. Host executable commands are explicit trusted host execution, not sealed package-closure proof. Consult the [SDK command reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) for shell bodies and task postconditions.

## Profile file checks

This complete workspace validates a captured shell configuration before writing its destination. It deliberately uses the host's `/bin/sh` syntax checker, so that executable is a prerequisite and trusted host input:

```typescript
import {
  check, defineWorkspace, exec, file, identity, lit, profile, repoFile,
  sourcePath, trackedCopyTo, workspace,
} from "@gripsack/core";

const syntax = check("shell-syntax", {
  subject: "dotfiles",
  run: exec({ argv: [lit("/bin/sh"), lit("-n"), sourcePath(".")] }),
});
const dotfiles = profile("dotfiles", {
  files: [file({
    source: repoFile("config/shell.sh"),
    content: identity(),
    destination: trackedCopyTo("~/.config/shell/settings.sh"),
    checks: [{ check: "shell-syntax", subject: "rendered", stage: "pre_flip" }],
  })],
});

export default defineWorkspace(() => workspace({ outputs: [syntax, dotfiles] }));
```

Create `config/shell.sh` with valid POSIX shell configuration, then use `grip check`, `grip plan dotfiles` and `grip apply dotfiles`, reviewing approvals and the deployment plan as usual. A check's `sourcePath(".")` is its immutable attached subject, not writable staging or an arbitrary working directory.

## Lifecycle boundaries

- A source check requires captured source.
- A rendered-file check must be `pre_flip` and validates before destination mutation.
- A deployed `pre_flip` check runs after candidate writes but before the generation flip, within journal compensation.
- `post_link` and `post_activate` run in the activation lifecycle. Late failure is not a promise of automatic rollback.
- A profile-bound check cannot also serve as a recipe validator or task postcondition.

Profile hooks are explicit lifecycle actions. They can have external effects, and an ambiguous interrupted delivery can run again with the same identity: write idempotent hooks and retain recovery data. See [safety](safety.md).

## Scheduling boundary

Scheduled registration and execution are not available. A successful `grip check` does not activate a timer. Use manual tasks for the actions documented here; an external scheduler remains your own operational choice and trust boundary.
