# Run logs

Gripsack initializes a structured log for command runs. Logs help explain
engine events; they are not a complete
transcript of every subprocess or a proof that a deployment succeeded.
Argument-parsing exits (such as `--help`) occur before logging, and a failure
to initialize logging can leave no run file.

## Where

```text
~/.local/share/gripsack/runs/<run-id>.jsonl   # one file per logged run
~/.local/share/gripsack/runs/latest          # symlink to the newest log
```

The state root is `$GRIPSACK_HOME` when nonempty, otherwise
`$XDG_DATA_HOME/gripsack` when set, otherwise the default above. The root
`run` span carries `run_id` and `command`; do not depend on the console
printing an id for every command. `latest` identifies the most recently
initialized log, not necessarily the last completed or failed command.
Save the specific filename when comparing concurrent runs.

## Privacy and retention

`grip` creates `runs/` at **0700** and each new log at **0600**, regardless of
the caller's umask. It tightens an existing caller-owned `runs/` before
writing. A symlink in place of the directory is refused, not followed.
`latest` is replaced atomically with a symlink to a generated basename; a
regular file at `latest` is left alone and logging does not start.

At startup and normal command exit, Gripsack keeps the **newest 100 completed
logs**, ordered by start time (run ID breaks ties). The current run, any
other run whose writer still holds its log lock, and the target of `latest`
are protected even outside that hundred. Killed writers release their locks;
the next pruning pass can reclaim their logs. This is a count, not a limit
on bytes or days. Save a private copy outside `runs/` if you need to keep a
particular log longer.

Only regular, singly linked files owned by the current user with a current
run ID and its matching opening record are eligible. Other entries, including
pre-0.57 logs, are neither removed nor counted. The tightened directory
protects access through `runs/` to old logs, but their individual modes are
unchanged; it cannot revoke an open descriptor or protect an outside copy.
Older binaries use different names and do not participate in locking; they
can still move `latest`. Locks coordinate Gripsack writers, not same-account
tools that rename files during cleanup. Archive or remove old logs yourself
after older writers have stopped. This policy never touches task-invocation
receipts, journals or generations.

## What's inside

Each line is a JSON event with `timestamp`, `level`, `fields.message` and,
where emitted, `fields.code`. `span` describes the current span and `spans`
is its ancestry: an array of **objects** with a `name` and structured fields,
not encoded span-name strings. Output or stage fields are present only
where the corresponding instrumentation emits them.

```bash
home=${GRIPSACK_HOME:-"${XDG_DATA_HOME:-"$HOME/.local/share"}/gripsack"}
L="$home/runs/latest"
jq -c 'select(.level == "ERROR")' "$L"
jq -c 'select(.fields.code != null)' "$L"
jq -c '{message: .fields.message, spans: .spans}' "$L"
```

The console defaults to warnings and errors on stderr; JSONL records info
and above. `GRIPSACK_LOG=debug grip check` enables debug console output,
but does **not** lower the JSONL layer's fixed info threshold. Machine-readable
command output such as `grip check --json` remains on stdout separately.

Logs are for diagnosis; recovery and garbage collection never read them.
Keep journals, generation manifests and retained content intact when
investigating a failed transition; see [safety](safety.md). Review logs for
private paths or command details before sharing them.

## For agents

The [debugging skill](https://github.com/gripsack-dev/gripsack/tree/{release_source}/skills/gripsack-debug)
provides a debugging workflow and diagnostic references. See [skills](skills.md)
for installation. Give the agent the specific run log and the failing command,
not only `latest`, which another command may replace. A completed evaluation is not a successful build or apply; read the
spans for the stage that actually failed.
