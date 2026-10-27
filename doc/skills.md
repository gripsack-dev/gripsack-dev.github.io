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

The [current adoption guide](https://github.com/gripsack-dev/gripsack/blob/d8d233c0738634fa79ae734bfdb76ad79c9917a4/skills/gripsack-adopt/SKILL.md)
is workspace-first, with explicit notes for existing legacy repositories. It
inventories the executable, version, configuration and ownership before choosing
packages, profiles, file policies, launchers and verification.

The tagged 0.48 source still contains the older legacy-oriented guide. Use the
reviewed postrelease documentation revision below for the updated instructions;
this does not change the released binary. Review the plan, exercise the actual
consumer and retain a tested recovery path. A successful command alone does not
prove full migration or reversibility.

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

Copy the skill directories from this reviewed documentation revision into your
agent harness's skills path (for example Claude Code). Read their contents
before granting execution authority. Installing guidance does not install or
upgrade the core.

```bash
skill_source=$(mktemp -d)
git -C "$skill_source" init --quiet
git -C "$skill_source" fetch --depth 1 https://github.com/gripsack-dev/gripsack d8d233c0738634fa79ae734bfdb76ad79c9917a4
git -C "$skill_source" checkout --detach FETCH_HEAD
mkdir -p ~/.claude/skills
cp -r "$skill_source/skills/gripsack-debug" ~/.claude/skills/
cp -r "$skill_source/skills/gripsack-adopt" ~/.claude/skills/
cp -r "$skill_source/.agents/skills/griplint-author" ~/.claude/skills/
cp -r "$skill_source/.agents/skills/gripfetch-author" ~/.claude/skills/
```
