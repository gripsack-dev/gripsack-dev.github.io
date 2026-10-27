# Safety

The boundaries below describe the 0.48 transaction and execution model,
not a claim that every assurance gate passed. The public
[core 0.48.0 release](https://github.com/gripsack-dev/gripsack/releases/tag/core-v0.48.0)
is **unsigned**: 17 practical local gates and 96 persistence partitions
passed; **TLC, TLAPS and Verus remain explicitly unqualified** for this
release. Existing proof sources and historical runs are not current
release qualification. 0.47 remains an unsigned, unverified prerelease.

The detailed admission boundaries and trusted components are recorded in
[`verification/guarantees.md`](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/verification/guarantees.md).
Linux and WSL2 on x86_64 are the supported host scope; this does not
qualify macOS or every Linux distribution. Report discrepancies between
these documented boundaries and the binary you use.

## The guarantee table

| Surface | Guarantee |
|---|---|
| Store object publication | atomic final-name rename; payloads land read-only |
| Generation selection | one atomic `current` flip (the link is validated to resolve under `$GRIPSACK_HOME/generations/`) |
| Generation contents | immutable once published (manifest + profile stage and rename in together); IDs are never reused, even across gc |
| Destination deploy / prune / rollback | journaled, postcondition-verified, crash-recovered; ownership lineage does not promote drift into managed content |
| Failed apply or rollback | compensation is attempted immediately; if the filesystem prevents it, the durable journal blocks further mutation until recovery completes |
| Tracked-copy drift | detected and **preserved by default**, in apply AND rollback |
| External tools and package-manager effects | adapter-dependent; effects outside journaled destinations are not automatically rolled back |
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
  journaled: gripsack refuses the mutation instead of recording a link
  it could not restore.
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

`gripfetch-*`, external `griplint-*` plugins and native tools are
**trusted code running with your privileges**. Fetched payload identity
checks do not make a malicious plugin harmless, and a checksum supplied
alongside a release is not an authenticated signature.

TypeScript evaluation uses a captured source bundle and provisioned Deno,
with restricted reads and no environment, network or subprocess grants.
This is not a sandbox for later native execution. Source approval binds
captured content and policy; it does not protect against privileged or
same-UID modification of trusted runtime storage. Fetching can access
credentials and host configuration.

Workspace file checks, task commands and profile hooks have distinct
lifecycle stages. A deployed `pre_flip` check can trigger journal
compensation; `post_link` and `post_activate` failures do not roll back
the committed generation. Native host commands can have effects beyond
managed files. See the
[0.48 SDK lifecycle reference](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md#file-checks-and-manual-tasks).

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

Recorded destination ownership does not migrate merely because a new
workspace wants the same path. `--take-over` is not a cross-identity
ownership transfer. For a current legacy generation `N`, 0.48 supports
an explicit reviewed `grip plan personal --migrate-from N`, followed by
`grip apply personal --migrate-from N`. Follow the
[migration guidance](workspace-migration.md) for its admission limits
and the separate legacy-prune alternative. Do not edit journals or
delete managed files to force migration.

## Explicit host-runtime dependence

A Linux GNU package may explicitly declare
`hostRuntime: { libraryDirectories: ["/opt/bb/lib64"] }` in `pkg(...)`.
This is a **package-scoped trust decision**, not a global filesystem
grant and not permission for evaluator code to read those directories.
A package closure with no such declaration retains the closed default,
including refusal of an undeclared absolute ELF RUNPATH.

Review both the package bytes and who controls the named host
directories. Roots compose only over the selected package's explicit
runtime-package dependency closure, in deterministic traversal and
declaration order. For example, a retained dependency library may use
its own declared host root; an unrelated package selected for the
same invocation cannot lend its policy to this closure. Directories
must be existing normalized absolute paths; canonical duplicate aliases
are refused. A dependency symlink may not escape its declared root.
Transitive ELF dependencies, ABI and search paths still undergo
admission. The existing narrow glibc SONAME allowance remains separate;
arbitrary `ld.so.cache`, `PATH` and ambient `LD_*` fallback are not
enabled. This is not an unsealed-execution switch or a substitute for
the [complete Conda closure](environments.md#complete-closures).

The fetched artifact's identity and the package's runtime-policy
identity remain distinct. Host libraries are host prerequisites, not
retained portable artifact content: declaring them does not copy them
into an OCI closure or authorize mounting them into BuildKit. Packages
with this policy are refused for portable image placement.

Persistent environment/profile wrappers for a package closure using
`hostRuntime` route through the core's managed runner. Each invocation
validates the retained package/descendant receipts and repeats native
admission against the current host libraries before sealed execution;
it does not persist a raw loader command as permanent authority.
Task/check execution and retained hook replay also repeat admission.
This does not make mutable host libraries immutable.

These wrappers retain the **absolute core executable location** and
the original private state path. Keep both installed and available.
Moving or removing the core or state makes the wrapper fail closed.
Restore the original stable core installation path, or reapply using
the core at its new installed location to recreate the projection.
Then use a fresh shell or explicitly source the managed profile again:
an existing shell's `PATH` can still select the old generation's
wrappers. Candidate0.46 qualification exercised this recovery on UBI8
glibc2.28 under a WSL2 kernel, including stdin and exit-status preservation.
Policy-free existing wrappers are unchanged.

For the separate guarantee about temporary storage and cross-device
store publication, see
[temporary files](settings.md#temporary-files-and-store-publication).

## What gripsack is not

gripsack is alpha software with a journaled transaction core, not a
backup system. Keep an independent backup of irreplaceable
configuration. The store is a cache of fetchable payloads plus prior
blobs — it is not the only copy of anything you cannot re-derive.

Read `grip plan` before applying and keep independent backups. This is
not qualification as the sole recovery boundary for an irreplaceable
home directory or for unattended fleet deployment. Install 0.48 manually
from the release archives: npm/crates.io publication is not part of this
release, and the signed installer/updater still fails closed on unsigned
artifacts.
