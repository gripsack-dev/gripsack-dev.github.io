# Agent guidance

Gripsack's source repository includes reusable guidance for agents that help inspect or operate a workspace. Guidance is not executable enforcement and does not grant permission to approve source, overwrite files or discard recovery data.

## Workspace adoption

The [gripsack-adopt skill](https://github.com/gripsack-dev/gripsack/tree/{release_source}/skills/gripsack-adopt) starts from the installed tools, configuration and ownership. Use it to choose package declarations, profiles, file policies, launchers and real consumer checks.

The [workspace guide](workspaces.md) and [SDK reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/typescript/README.md) are the public API reference. An agent should not invent constructor names or assume a successful plan has deployed anything.

## Debugging

The [gripsack-debug skill](https://github.com/gripsack-dev/gripsack/tree/{release_source}/skills/gripsack-debug) explains structured logs, span chains and diagnostic codes. Give the agent the failing command and exact run-log filename rather than only `latest`, which another invocation may replace.

Logs are diagnostic evidence, not recovery authority. Keep journals, generation manifests and retained state intact while investigating. See [run logs](runs.md) and [safety](safety.md).

## Use with your agent

Review the skill contents at the selected source revision, then copy the chosen skill directory into your harness's configured skill path. For Claude Code, for example, that can be `~/.claude/skills/`. Installing guidance does not install or upgrade `grip`.

Require the agent to review captured source and policy, inspect a plan before applying, and report only checks it actually ran. A task receipt, evaluation result and application-level consumer test answer different questions.
