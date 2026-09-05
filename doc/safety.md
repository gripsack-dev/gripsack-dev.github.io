# Safety

What gripsack guarantees, precisely — separated by surface, because
"safe" is not one property. Everything on this page is enforced by
test: the transaction invariants are also machine-checked (the
journal protocol as an exhaustive state-machine model plus a
TLC-checked TLA+ spec — [plan 0028](https://github.com/gripsack-dev/gripsack/tree/main/plan/0028-machine-checked-model.md)).

If anything on this page ever disagrees with the binary in your hand,
that is a release-blocking bug — please file it.

## The guarantee table

| Surface | Guarantee |
|---|---|
| Store object publication | atomic final-name rename; payloads land read-only |
| Generation selection | one atomic `current` flip |
| Generation contents | immutable once published (manifest + profile stage and rename in together); IDs are never reused, even across gc |
| Destination deploy / prune / rollback | journaled, postcondition-verified, crash-recovered |
| Failed apply or rollback | restores the captured prior state before returning |
| Tracked-copy drift | detected and **preserved by default**, in apply AND rollback |
| External package-manager effects (brew/pixi/apt) | adapter-dependent, best effort — never auto-rolled-back |
| Arbitrary `run` steps | not automatically reversible (plan output says so) |

## Journaled transitions

Every mutation of a managed destination — deploy, prune-on-undeclare,
rollback — records its prior state AND its intended end state, durably,
before the mutation. After the mutation, the destination is re-read
through the same pinned directory handle and must equal the intent, or
the run fails and compensation restores the prior. The generation flip
is the single commit point; nothing commits unverified.

Recovery is exact-equality: a run is committed iff `current` equals
its target generation, uncommitted iff it equals the previous one —
anything else is corruption and blocks, with the journal retained.

## What recovery restores exactly

- **File bytes** — from the content-addressed prior store (deduped,
  write-once).
- **Unix mode** — the recorded mode rides the restore (a 0600 secret
  replaced by a symlink mid-run comes back 0600, not umask-default).
- **Symlink targets** — verbatim. A non-UTF-8 target cannot be
  journaled today: gripsack refuses the mutation loudly instead of
  recording a link it could not restore. (Byte-exact preservation is
  on the roadmap.)
- **Nothing else** — mtimes, ownership, xattrs are outside the model
  by design.

A crash between a mutation and its commit, followed by *your* edit,
keeps your edit. The drift guard reads three ways: landed-intact →
restore prior, never-landed → nothing to do, anything else → yours.

## The GC safety model

`grip gc` never removes the current generation or anything any
retained generation references (store paths AND prior blobs). It
fails closed: an unreadable generations inventory, a corrupt manifest,
or a current generation missing from disk all abort before the first
deletion. Uncertainty means do nothing. `--dry-run` previews the exact
deletion plan.

## Corrupt persisted state

A generation is validated when read, not trusted because it parses:
embedded number must equal its directory, destinations must be unique
(case-folded), hashes well-formed, store paths confined to
`$GRIPSACK_HOME/store`. A current generation whose manifest is
unreadable blocks every mutating command. Corrupt journal entries
quarantine into `journal/quarantine/` and block mutation until
inspected — recovery metadata is never silently discarded.

## Plugin and tool trust

`gripfetch-*` plugins and provisioned tools (deno, pixi) are **trusted
code running with your privileges**. Hash verification protects store
contents — every fetched byte is checked against the lockfile before
it enters the store — it does not make a malicious plugin harmless.
The credential boundary is eval: TypeScript module evaluation runs
sandboxed (no env, no network, no subprocesses) and sees no
credentials; fetching necessarily can. The lockfile is the sole
source of pinning; a tampered pin fails the hash check at apply.

## What gripsack is not

gripsack is alpha software with a journaled transaction core, not a
backup system. Keep an independent backup of irreplaceable
configuration. The store is a cache of fetchable payloads plus prior
blobs — it is not the only copy of anything you cannot re-derive.

Recommended today: dogfood freely, read `grip plan` before applying,
keep the backup. Not yet: sole recovery boundary for an irreplaceable
home directory, unattended fleet deployment.
