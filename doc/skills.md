# Skills

Installable agent skills — teach your agent to operate and migrate
gripsack environments by reading the repo, not by guessing.

## gripsack-debug

Diagnose a failing run from its structured log. Every `grip` invocation
writes JSONL with run ids and span-based causality to
`~/.local/share/gripsack/runs/`; this skill teaches an agent to read
it: field tables, span chains, jq filters, the diagnostic-code table,
and the debugging loop.

## gripsack-adopt

Migrate an existing tool into a module, interview-style. The agent
inventories the tool (binary location, version, config paths, install
method), asks only the questions it can't answer from the system —
pinning policy, config ownership mode per file — writes the module,
and proves it: `plan` clean, apply works, second apply satisfied.

## Install

Copy the skill directory into your agent harness's skills path
(e.g. `~/.claude/skills/` for Claude Code, or your equivalent):

```bash
git clone --depth 1 https://github.com/gripsack-dev/gripsack /tmp/gripsack
cp -r /tmp/gripsack/skills/gripsack-debug ~/.claude/skills/
cp -r /tmp/gripsack/skills/gripsack-adopt ~/.claude/skills/
```
