# Review and saved plans

Source approval, semantic review and deployment planning answer different questions. Approval binds captured bytes and policy; semantic review explains declared changes; a plan describes the selected operation. None proves that arbitrary commands are safe.

## Snapshot and compare

First apply the [file-only workspace](workspaces.md) through its ordinary reviewed workflow. These commands compare retained generations, not unevaluated source edits. Keep snapshots outside the captured repository:

```sh
grip snapshot current --out /tmp/gripsack-before.json
# Deliberately edit, review, plan and apply your workspace through the ordinary workflow.
grip diff /tmp/gripsack-before.json current --json
```

Selectors include `current`, `generation:N`, `snapshot:FILE`, a bare snapshot filename and `proposed:IRFILE`. The proposed selector consumes already-emitted IR with the repository's `gripsack.lock` offline; it is not another hand-authored configuration format or permission to execute it. Snapshots are private files (mode `0600`).

Semantic review is offline: it does not evaluate TypeScript, fetch packages, start services, run tasks or change generations. New generations retain private immutable declaration/dependency evidence, actual evaluation facts and probes, selected captured inputs, locks and available artifact receipts. Rollback and comparison read that frozen evidence rather than today's checkout. An unchanged or provenance-only apply reuses prior evidence instead of rewriting history.

Older generations without retained review artifacts remain readable but incomplete. Missing declarations, probes, locks, receipts and redacted values remain unknown, even in a self-comparison; they are not inferred from current source.

For `diff` and `diff-config`, exit 0 means complete and unchanged, 2 complete and changed, 3 incomplete (including fallback), and 1 an error. Automation must distinguish these results rather than treating incomplete comparison as equality.

## Configuration views

```sh
printf '{"enabled":true}\n' > /tmp/gripsack-before-config.json
printf '{"enabled":false}\n' > /tmp/gripsack-after-config.json
grip diff-config /tmp/gripsack-before-config.json /tmp/gripsack-after-config.json --format json --json
```

These inputs are actual configuration files, not semantic snapshots or selectors. This example exits 2 because the complete comparison found a change.

Choose `--format json`, `toml` or `bytes`. JSON and TOML parsing are strict; explicit bounded byte fallback is not a successful structured comparison. Portable output omits raw configuration values. `--local-values` opts into local value display: treat its output as sensitive and do not paste it into public logs. Missing evidence remains unknown rather than an invented no-change result.

For live planning, use `grip plan dotfiles --json`: this explicitly performs normal trusted evaluation and reports selected deployment operations and bounded configuration views. Its successful exit code does not imply complete evidence; inspect `complete`, configuration unknowns and change completeness. Structural equality is not application equivalence and does not hide exact byte differences.

## Save a deployment plan

```sh
grip plan dotfiles --save /tmp/gripsack-dotfiles-plan.json
grip apply --saved-plan /tmp/gripsack-dotfiles-plan.json
```

Review the plan before the second command. Save outside the captured repository so writing the plan does not stale its own source binding. The private plan retains exact admitted IR and can contain authored literal configuration; never put secrets in service literals. Inherited secret references are not resolved or stored while saving.

Saving does not grant execution authority. Saved apply checks source, lock, trust, facts, probes, base generation, scope and destination bindings. A stale plan is refused; make a new plan rather than forcing it or silently evaluating different source. Existing ownership, crash recovery and per-mutation checks still apply. External filesystem writers can race operating-system operations.

Review and saved profile application do not implicitly start unrelated [services](services.md). Profile rollback is not rollback of database data or task effects. See [safety](safety.md) for the underlying boundaries.
