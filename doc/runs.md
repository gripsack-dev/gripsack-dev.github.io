# Run logs

Every `grip` invocation is written down. If something fails, you (or an
agent helping you) never have to guess what the engine did.

## Where

```
~/.local/share/gripsack/runs/<run-id>.jsonl   # one file per run
~/.local/share/gripsack/runs/latest           # symlink to the newest
```

(`$GRIPSACK_HOME` if set.) Console output names the run id; every event
carries it.

## What's inside

One JSON object per line: `timestamp`, `level`, `fields.message`,
`fields.code` for coded diagnostics, and `spans` — the ancestry chain
that makes causality explicit. `["run", "plan", "module:helix"]` means
"this event happened inside helix, inside plan, inside this run." To
see why something happened, walk up the chain; to see what something
caused, grep for events containing its span.

```bash
L=$(readlink ~/.local/share/gripsack/runs/latest)
jq -c 'select(.level == "ERROR")' "$L"          # every error
jq -c 'select(.fields.code != null)' "$L"       # every coded diagnostic
```

The console shows warnings and errors by default; the JSONL always
records info and up. `GRIPSACK_LOG=debug` for the full stream on the
console too.

## For agents

`skills/gripsack-debug/` in the
[gripsack repo](https://github.com/gripsack-dev/gripsack/tree/main/skills/gripsack-debug)
is an installable skill that teaches an agent all of this: the field
table, span-chain causality, jq filters, the diagnostic code table, and
the debugging loop. Hand a failing build to your agent with the skill
installed and it reads the run log instead of guessing.
