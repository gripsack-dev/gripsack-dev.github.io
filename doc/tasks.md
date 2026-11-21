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

`status` and `log` look up that ID in the current Gripsack state home. Neither
needs a checkout, evaluates a workspace, or clones a repository. Both ignore
`--repo`, even if the named checkout no longer exists. `list` and `plan`
still inspect a local workspace, and `run` still resolves its repository.

The saved log is bounded: if any output was omitted, human `status` and
`log` warn on **stderr**, not in the log text on stdout. For automation, read
`logs_truncated` from `task status --json` or `truncated` from `task log
--json`. The warning does not change the task outcome. Review private
stdout/stderr before sharing it.

Since core 0.56, ordinary `grip task run` labels each dependency's steps and
postcondition checks on stderr as they start and finish. Child stdout streams
immediately, including partial lines, and remains unchanged for pipelines.
Stderr from each child is still bounded capture, printed when that process
finishes; it is not a live stderr stream. Unterminated output is separated from
status lines. `--json` keeps its structured stdout and bounded log behavior.

`grip apply` already reports live progress and separate check/hook blocks
(since 0.54). Passing verification output is collapsed by default; `--verbose`
shows the full captured block, and failures show their captured output. Capture
is per verification, not across the entire apply. Piped/`NO_COLOR` metadata is
plain; a tool's own raw task stdout may still contain its own formatting.

## Archiving task history

Each invocation needs two entries in `task-invocations`: `<id>.json` and
`<id>.log`. New invocations are refused when those entries would take the
directory over 10,000 entries. Nothing is pruned. To make room, archive
completed pairs you no longer need in online task or scheduled-job history.

Work as the owner of the private state home, without other operators moving
or restoring history. Select **one** exact ID from a previous run or a
receipt filename. An eligible version-1 receipt must be readable with
`grip task status <id> --json`, match its filename, have `root_retained:
false`, and have a terminal status: `succeeded`, `failed`, `blocked`,
`cancelled` or `skipped-busy`. Require the matching readable regular log,
even if it is empty. **Leave everything else in place**: running work is
recorded as `indeterminate`, and that same status can outlive the process.
Age, a vanished PID, and a nonzero status-command exit code are not evidence
of completion. Never move a retained root, an incomplete pair, a symlink,
a malformed or unfamiliar record, or any lock, process root or staging data.

With Bash and `jq`, set `invocation` to the ID you reviewed. This example
checks the pair, then moves just those two files into a **new private
sibling directory** on the same filesystem:

```bash
(
  set -eu
  umask 077
  home=${GRIPSACK_HOME:-"${XDG_DATA_HOME:-"$HOME/.local/share"}/gripsack"}
  id=${invocation:?set invocation to the exact reviewed invocation ID}
  [[ $id =~ ^[0-9a-f]{64}$ ]] || exit 1
  base="$home/task-invocations/$id"
  for path in "$base.json" "$base.log"; do
    [[ -f $path && ! -L $path ]] || exit 1
  done
  # status returns the recorded outcome, not just lookup success.
  record=$(grip task status "$id" --json) || case $? in
    1|3|75|130) ;; *) exit 1 ;; esac
  jq -e --arg id "$id" '
    .version == 1 and .invocation == $id and .root_retained == false and
    (.status as $s | ["succeeded","failed","blocked","cancelled","skipped-busy"] | index($s) != null)
    and all(.nodes[]; .status != "indeterminate")
  ' <<< "${record:?no validated receipt}" >/dev/null || exit 1
  grip task log "$id" >/dev/null || exit 1
  archive=$(mktemp -d "$home/task-archive.XXXXXXXX") || exit 1
  printf 'Archive destination: %s\n' "$archive"
  archive_dev=$(stat -c %d -- "$archive") || exit 1
  for path in "$base.json" "$base.log"; do
    source_dev=$(stat -c %d -- "$path") || exit 1
    [[ $source_dev == "$archive_dev" ]] || exit 1
  done
  mv "$base.json" "$base.log" "$archive/"
)
```

Keep the archive private; these are the original bytes, not sanitized terminal
output. The two moves are not atomic as a pair. If interrupted, stop and
locate both halves at the printed destination and their original paths before
retrying. Never overwrite a file or discard an unmatched half. After both
files move, their two slots are available to a new invocation. The archived
ID is no longer available through `grip task status`/`log` or scheduled
history in that store. If no pair qualifies, do not force admission by moving
unknown evidence.

## Dependencies and mutation

`deps` names unordered prerequisite tasks that must succeed in the same invocation. A task's `steps` are ordered locally; `checks` are its invocation postconditions. Declare live mutation paths with `context: { kind: "host", mutable_paths: [...] }` and shared mutation keys with `locks: [lock("user", "editor-config")]` or store-scoped locks.

Locks coordinate declared effects; they do not grant execution authority or infer dependencies from shell text. `--skip-busy` can skip an active conflict, not bypass an unknown interrupted owner. `--timeout-seconds` bounds realization, prerequisites and verification together. Interrupted or indeterminate outcomes are not recorded as success.

Use typed `packageCommand`, `lit` and explicit `env`/`argv` values for commands. A `runBash` body requires a declared package-command interpreter; it does not discover ambient Bash. Host executable commands are explicit trusted host execution, not sealed package-closure proof. Consult the [SDK command reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) for shell bodies and task postconditions.

## Literal Bash bodies

Create this complete `gripsack.ts` in a separate example directory:

<!-- example: examples/workspaces/11-bash-task/gripsack.ts -->
```typescript
import {
  bash, conda, defineWorkspace, environment, lit, packageCommand,
  pkg, provider, targetPlatform, task, workspace,
} from "@gripsack/core";

const target = targetPlatform({ os: "linux", arch: "x86_64" });
const shell = pkg("shell", {
  producer: provider(conda.environment({
    channels: ["conda-forge"],
    packages: { bash: "*" },
    systemRequirements: {
      libc: { family: "glibc", version: "2.28" },
      linux: "4.18",
    },
  })),
  commands: { bash: "bin/bash" },
  target,
  layout: { kind: "prefix_materialized" },
});
const dev = environment("dev", { packages: ["shell"], target });
const greet = task("greet", {
  environment: "dev",
  steps: [
    bash`printf '%s\n' "$MESSAGE"`
      .interpreter(packageCommand("shell", "bash"))
      .env("MESSAGE", lit("two words"))
      .build(),
  ],
});
export default defineWorkspace(() => workspace({ outputs: [shell, dev, greet] }));
```

Run `grip update`, review the source and lock approvals, then `grip task run greet --closed-stdin`. The normal lock pins the interpreter package. Bash runs with fixed `-e -u -o pipefail`; it is not ambient shell discovery. The tag accepts literal bodies, not JavaScript substitutions: pass dynamic values through typed environment bindings. To author shell `${NAME}` syntax inside the tag, escape the dollar sign as `\${NAME}`. JavaScript evaluates substitutions before a tag is called, so rejection is not a sandbox for JavaScript side effects.

The same command works in task steps, check runs and hook runs. Use `runBash({ interpreter, body, env, cwd })` with a separately declared tagged body when composing reusable commands; `cwd` must be a typed path. See the SDK reference for the complete command contract.

## Profile file checks

This complete workspace validates a captured shell configuration before writing its destination. It deliberately uses the host's `/bin/sh` syntax checker, so that executable is a prerequisite and trusted host input:

<!-- example: examples/workspaces/12-file-check/gripsack.ts -->
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
- A profile-bound check cannot also serve as a task postcondition.

Profile hooks are explicit lifecycle actions. They can have external effects, and an ambiguous interrupted delivery can run again with the same identity: write idempotent hooks and retain recovery data. See [safety](safety.md).

## Scheduling boundary

[Scheduled tasks](schedules.md) register only through explicit profile application with a supported user service manager. `grip check` never activates a timer. Tasks with `services: ["postgres"]` require an already-healthy [service](services.md); task invocation does not implicitly run `grip up`.

## Typed artifact selectors

In core 0.55, package command exports and profile artifact origins expanded release tokens, but `artifact(output, selector)` in command arguments, env or cwd joined the selector literally. Core 0.56 makes these typed references consistent: each selector expands using the referenced package's frozen source version and the release asset platform spellings. This applies in task steps, check runs, hook runs, attached file-check commands and scheduled task commands, as well as environment-level `env`.

For a package releasing a shared library named `libflyline.so.<version>`, this focused check declaration tests the concrete filename. It is a fragment, not a complete workspace: import `artifact`, `check`, `exec` and `lit`, declare a release-backed package named `flyline` with `commands: {}` whose selected payload root contains that library, and register the check alongside it in `workspace.outputs`. A paired profile file consumer can use `artifactFile("flyline", "libflyline.so.{version.bare}")` with the same selector. `/usr/bin/test` is an explicit trusted host executable prerequisite.

```typescript
const flylineSoPresent = check("flylineSoPresent", {
  subject: "flyline",
  run: exec({
    argv: [
      lit("/usr/bin/test"),
      lit("-f"),
      artifact("flyline", "libflyline.so.{version.bare}"),
    ],
  }),
});
```

Use this package-subject check as a task postcondition with
`checks: ["flylineSoPresent"]`, then run that task. Registering a check in
`workspace.outputs` alone does not execute it; `grip check` validates declarations
rather than running check commands.

For a locked tag `v1.2.3`, the selector is exactly `libflyline.so.1.2.3`. `{version}` would retain `v1.2.3`; `{version.bare}` removes exactly one lowercase `v`, not an uppercase `V` or every leading `v`. There is no alternate raw/bare filename search. A later lock-only update moves this selector with `flyline`, not with the check's environment or another package. This checks file existence, not whether a dynamic loader can load the library.

Because this check's subject is the package `flyline`, `sourcePath("libflyline.so.{version.bare}")` is an alternative to the explicit `artifact` reference (import `sourcePath` to use it). Package-subject `sourcePath` selectors in argv, env and cwd bind to the subject's own lock. An attached **file** check still allows only `sourcePath(".")`; a file has no child namespace.

The same typed `artifact` value can be used in `exec`'s `env: { LIBRARY: artifact("flyline", "libflyline.so.{version.bare}") }`. A `cwd: artifact("tool", "tool-{version.bare}")` selects a directory from `tool` using **tool's** locked version. Environment-level `env` uses this same binding policy. `artifact("flyline", ".")` selects the whole artifact; selectors are relative to the selected payload root, after any `archiveRoot` selection.

Literal argv/env/cwd values and Bash bodies remain literal. For example, `lit("libflyline.so.{version.bare}")` stays that exact string; it is not equivalent to a typed `artifact` reference inside argv. Shell bodies gain no JavaScript or release-token interpolation. Host/repository paths, input names and writable staging selectors remain literal too.

Missing required versions, unknown tokens and unsafe expanded relative paths fail with declaration provenance. Expansion precedes filesystem selection, which checks canonical containment even for cwd. Text plans and JSON `resolved_paths` show concrete typed selectors from admitted lock evidence without fetching payloads or asserting existence. Retained hooks, launchers and portable bindings use concrete selectors; historical portable literal selectors are not reinterpreted against a future lock.

Scheduled jobs resolve these selectors before capturing the task. Replay uses
the recorded concrete paths without consulting today's lock. Older snapshots
keep their literal selector meaning, including filenames containing braces.
