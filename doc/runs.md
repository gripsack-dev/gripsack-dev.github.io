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

Logs are diagnostic evidence, not retention roots or recovery authority.
Keep journals, generation manifests and retained content intact when
investigating a failed transition; see [safety](safety.md). Review logs for
private paths or command details before sharing them.

## For agents

The [debugging skill](https://github.com/gripsack-dev/gripsack/tree/{release_source}/skills/gripsack-debug)
provides a debugging workflow and diagnostic references. See [skills](skills.md)
for installation. Give the agent the specific run log and the failing command,
not only `latest`, which another command may replace. For captured-source
approval and evaluation receipts, use the separate [source-trust guidance](safety.md);
a completed evaluation receipt is not a successful build or apply receipt.
