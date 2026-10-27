# Skills

Installable agent guidance for reading and operating gripsack, not
executable enforcement or proof that a deployment is safe. Prefer new
IR8 workspaces; use the
[0.48 SDK reference](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md)
as API authority when a skill contains older examples.

## gripsack-debug

Read structured run logs: run IDs, span chains, jq filters and diagnostic
codes. The default state location is `~/.local/share/gripsack/runs/`;
use the actual `GRIPSACK_HOME` when configured. Logs are diagnostic
evidence, not proof that every requested effect completed.

## gripsack-adopt

This shipped skill targets the **legacy host/module workflow**. It
inventories a tool's binary, version, config paths and install method,
then helps choose pinning, ownership and verification. Some bundled
examples predate the workspace API; do not copy their Pixi/build advice
into a new workspace. Use workspace packages, profiles, file policies
and named checks from the SDK reference instead. Review the plan,
exercise the intended consumer and inspect a second apply; a successful
command alone does not prove full migration or reversibility.

## griplint-author

Author a config linter as a **data pack** in `crates/griplint/packs/`:
research the tool's config surface end to end (official docs first,
schemas and parser source over memory — never guess a key), write the
versioned key table as TOML data, and pin behavior with the golden
fixture corpus. The reference pack is `helix.toml`. Exotic formats
(RON, KDL, custom) stay external plugins — prove those against
[griplint-conformance](https://github.com/gripsack-dev/griplint-conformance),
the contract made executable; the suite drives your plugin exactly
like the core does.

## gripfetch-author

Author a `gripfetch-*` transport plugin — an internal registry, a
distro mirror, anything with an mTLS or credentialed dance. The skill
teaches the protocol contract: one JSON request on stdin (`locked`
present = reproduce exactly, absent = resolve and pin), NDJSON
progress/diagnostics/response on stdout, and the reproducibility bar
the store's hash verification enforces. Prove it:
[gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance)
— the contract made executable; the suite drives your plugin exactly
like the core does.

## Install

Copy the skill directories from the matching release into your agent
harness's skills path (for example Claude Code). Review their contents
before granting an agent execution authority; installing guidance does
not install or upgrade the core.

```bash
git clone --depth 1 --branch core-v0.48.0 https://github.com/gripsack-dev/gripsack /tmp/gripsack
mkdir -p ~/.claude/skills
cp -r /tmp/gripsack/skills/gripsack-debug ~/.claude/skills/
cp -r /tmp/gripsack/skills/gripsack-adopt ~/.claude/skills/
cp -r /tmp/gripsack/.agents/skills/griplint-author ~/.claude/skills/
cp -r /tmp/gripsack/.agents/skills/gripfetch-author ~/.claude/skills/
```
