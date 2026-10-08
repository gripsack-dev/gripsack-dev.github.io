# Safety

What gripsack guarantees, precisely — separated by surface, because
"safe" is not one property. Everything on this page is enforced by
test: the transaction invariants are also machine-checked (the
journal protocol as an exhaustive state-machine model plus a
TLC-checked TLA+ spec — [plan 0028](https://github.com/gripsack-dev/gripsack/tree/main/plan/0028-machine-checked-model.md)),
and the decision kernels they lean on — commit classification,
ownership authority, GC retention, the merge splice, build closures,
and the scheduler's readiness/release/latch decisions — are proved by
Verus, one implementation serving production and the verifier. The
per-guarantee ledger with admission boundaries, trusted components
and calibrations:
[`verification/guarantees.md`](https://github.com/gripsack-dev/gripsack/tree/main/verification/guarantees.md).

If anything on this page ever disagrees with the binary in your hand,
that is a release-blocking bug — please file it.

## The guarantee table

| Surface | Guarantee |
|---|---|
| Store object publication | atomic final-name rename; payloads land read-only |
| Generation selection | one atomic `current` flip (the link is validated to resolve under `$GRIPSACK_HOME/generations/`) |
| Generation contents | immutable once published (manifest + profile stage and rename in together); IDs are never reused, even across gc |
| Destination deploy / prune / rollback | journaled, postcondition-verified, crash-recovered; ownership lineage (origin survival, no drift
  promotion) holds the same machine-checked standard since 0.25 |
| Failed apply or rollback | compensation is attempted immediately; if the filesystem prevents it, the durable journal blocks further mutation until recovery completes |
| Tracked-copy drift | detected and **preserved by default**, in apply AND rollback |
| External package-manager effects (brew/pixi/apt) | adapter-dependent, best effort — never auto-rolled-back |
| Activation intents (caches, services, custom hooks) | durable intent before the flip; ambiguous interrupted delivery may run again with the same identity, so hooks must be idempotent; durable terminal outcomes are not automatically retried; post-activation failure never rolls back. Explicit rollback is a new activation and may execute the retained generation's hooks |
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

## Unattended approval

Approval binds the **exact captured source bundle and policy** — the
digests, not the directory. A fresh ephemeral machine has no TTY and
no interactive history, and that is fine: the decision moves
out-of-band, the machine only compares digests.

The workflow:

1. **Keep the reviewed source immutable** — a commit, or an archive
   you reviewed and kept. Review the inventory it captures: the
   generated lockfile, captured untracked files,
   [capture exclusions](settings/reference.md#capture-envtoml-only).
2. **Record the expected digests out-of-band** — the `.bundle_digest`
   and `.policy_digest` of exactly what you reviewed.
3. **On the machine, compare before approving**, using the recipe below.
4. **Stop on mismatch.** A differing digest means the captured source
   changed since review — re-review the changed inventory, then
   approve the exact new digests. Never auto-approve whatever
   `inspect` returns.

```sh
set -eu
: "${expected_bundle:?load the separately reviewed bundle digest}"
: "${expected_policy:?load the separately reviewed policy digest}"
source=$(grip trust inspect --json)
[ "$(printf '%s' "$source" | jq -er .bundle_digest)" = "$expected_bundle" ] &&
  [ "$(printf '%s' "$source" | jq -er .policy_digest)" = "$expected_policy" ] ||
  { echo "captured source differs from review — NOT approving" >&2; exit 1; }
grip trust add --bundle "$expected_bundle" --policy "$expected_policy"
grip check
```

The shell recipe requires `jq`; the two expected values must arrive
through your reviewed deployment configuration, **not** assignments
from the `inspect` command in this script. Keep that configuration
outside the captured checkout. Compare the policy as well as the
bundle: frontend/runtime identity and capture policy are part of the
approval decision. A reviewed source edit permits evaluation; it
does not waive the separate frozen-input check. For example, after
reviewing a changed Pixi manifest or lock, `grip check` still refuses
its stale imported identity until an explicit `grip update`, review
of the resulting `gripsack.lock`, and renewed exact-digest approval.

Measured with the promoted 0.45.0 binary: a separately recorded
reviewed pair matched and allowed `check`; byte changes to
`gripsack.lock`, `pixi.lock`, or `[capture].exclude` stopped before
`trust add` or evaluation. Trust records and evaluation receipts
remained byte-identical on each mismatch. A wrong expected policy
also stopped even when the expected bundle still matched. These are
fixture-level observations, not blanket fleet-deployment
qualification.

Boundaries that hold everywhere:

- Never `GRIPSACK_TRUST_ALL` — `=1` is refused, not an approval workflow.
- No repo-wide or floating approval exists. One approval at the repo
  root covers nested directories, but changed captured content is a
  new approval decision — including a lockfile write between updates.
- Inspection and approval themselves evaluate nothing; a change
  between inspect and approve fails approval rather than blessing
  newer bytes.

This is still a human decision per content change — "unattended"
means no prompt, not unreviewed.

## The destination boundary

gripsack enforces one hard boundary: nothing may deploy INTO the env
repo checkout. Destinations are otherwise your paths at your
privileges — absolute paths outside `$HOME` (e.g. `/usr/local/bin`)
are allowed and in real use. The residual race we know about: there is
no portable atomic content-compare-and-swap (`renameat2
RENAME_EXCHANGE` is Linux-only), so between a drift decision and the
write there is a microsecond window — every journaled mutation
re-validates the live object at that boundary and aborts retryably on
mismatch rather than clobbering it.

Putting a launcher in `/usr/local/bin` does not make its private
package store a multi-user installation. The documented
[environment launchers](environments.md#destinations-personal-and-shared)
run as the same UID that owns and deploys the environment. Do not
make all of `GRIPSACK_HOME` world-readable or writable to let another
UID reach it: trust records, journals and retained generations remain
private authoritative state.

## What gripsack is not

gripsack is alpha software with a journaled transaction core, not a
backup system. Keep an independent backup of irreplaceable
configuration. The store is a cache of fetchable payloads plus prior
blobs — it is not the only copy of anything you cannot re-derive.

Recommended today: dogfood freely, read `grip plan` before applying,
keep the backup. Not yet: sole recovery boundary for an irreplaceable
home directory, unattended fleet deployment.
