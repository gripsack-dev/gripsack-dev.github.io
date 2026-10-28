# Safety and recovery

Gripsack makes source approval, file ownership and retained state explicit. Review the plan, keep independent backups of irreplaceable configuration, and exercise the actual consumer before discarding recovery data. It is alpha software, not a whole-machine backup system.

## What is protected

| Surface | Boundary |
|---|---|
| Store publication | Verified content is sealed read-only and published by final-name rename |
| Generation selection | One atomic `current` flip selects the generation |
| Managed destination changes | Journaled prior/intended state with postcondition checks and crash recovery |
| Failed pre-commit transition | Compensation is attempted; unresolved recovery blocks further mutation |
| Tracked-copy drift | Preserved by default in apply and rollback |
| Retained generations | Keep their package roots and prior-state blobs available |
| Native tasks, hooks and external tools | Effects outside journaled destinations are not automatically undone |

Destination changes are not atomic across a whole profile. Stop dependent consumers when a transition requires uninterrupted file or command availability. The generation flip is a commit boundary, not a guarantee that no intermediate destination state was observable.

## Source approval

Evaluation uses a captured source bundle and provisioned Deno with restricted reads and no environment, network or subprocess grants. Approval binds the **exact bundle and policy**, including captured inputs, frontend/runtime identity and capture exclusions.

```sh
grip trust inspect --json
grip trust add
```

Interactive approval displays inventory and policy for review; inspect actual changed content too. Profile selection and `--focus` narrow deployment or display, not approval authority. A lockfile write or an out-of-focus source change still requires review. Inspection and approval themselves do not evaluate workspace code.

The evaluator restriction is not a sandbox for later native execution. Package tools, explicit host commands and helper executables run with their declared authority and your privileges. A checksum does not make malicious code safe. Same-UID or privileged modification of trusted runtime storage is outside this protection.

## Unattended approval

Record expected bundle and policy digests **separately from the machine operation**, after reviewing the source. Compare both before approving:

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

This requires `jq`. Do not derive the expected values from the inspection being approved. Keep deployment configuration outside the captured checkout. Stop and re-review on a mismatch; a change between inspection and approval also fails closed.

There is no floating repository-wide approval. `GRIPSACK_TRUST_ALL=1` is refused. Approving a changed Pixi manifest/lock permits evaluation but does not waive frozen-input checks: explicitly import it with `grip update`, review the resulting lock, then approve the new capture.

## File ownership and journal recovery

Every journaled mutation records prior state and intended end state before changing the destination. It re-reads the result through a pinned directory handle and checks the postcondition. Before commit, failed changes trigger compensation; unresolved recovery retains the journal and blocks later mutation.

Recovery covers recorded file bytes, Unix modes and symlink targets, not mtimes, ownership or extended attributes. Drift is not promoted to managed content merely because a previous transition was interrupted. A changed live file is preserved rather than blindly replaced with the prior snapshot.

The current-generation pointer must equal the recorded previous or target generation for recovery to decide its state. Unexpected state blocks rather than guessing. Corrupt manifests and quarantined journal entries remain visible recovery problems, not disposable cache files.

Recorded ownership does not transfer merely because another workspace wants the same path. `--take-over` is a deliberate foreign-file adoption permission, not blanket ownership reassignment. Do not delete managed files, journals or manifests to force admission. See [profile ownership](adopting.md).

## Hooks and checks

Rendered-file checks run before destination mutation. Deployed `pre_flip` checks run after candidate writes but before commit, within compensation. `post_link` and `post_activate` failures do not automatically roll back a committed generation.

Hooks have durable activation intents. Ambiguous interrupted delivery can run again with the same identity, so hooks must be idempotent. Terminal outcomes are not automatically retried. Explicit rollback is a new activation and may run the retained generation's hooks. Arbitrary task, service and external-tool effects are not reversed by restoring managed files.

See [tasks and checks](tasks.md) for lifecycle stages and invocation receipts.

## Host runtime dependencies

Linux GNU packages may declare `hostRuntime: { libraryDirectories: ["/opt/vendor/lib64"] }`. Review who controls those directories as well as the package bytes. This is package-scoped runtime authority, not an evaluator read grant, arbitrary ambient loader fallback or a BuildKit mount grant.

The dependency graph, ABI and search paths are re-admitted on invocation. Host libraries remain mutable trusted host inputs; they are not retained portable artifacts. Packages with this policy are refused for portable image placement. Prefer complete retained package closures when portability matters.

Managed launchers retain the absolute installed core location and private state path. Keep both available. If the core moves, restore it or reapply using the replacement binary; do not edit launcher bodies. Putting a launcher in a shared directory does not make private state a multi-user installation. Run as the owning UID and keep trust, journals and retained state private.

## Retention and garbage collection

```sh
grip generations
grip gc --dry-run
```

GC does not remove the current generation or content referenced by retained generations and recovery roots. Unreadable inventory, corrupt manifests or missing current state stop reclamation before deletion. Keep predecessor generations, captured prior blobs and unresolved recovery data until you have checked deployed behavior and recovery.

`grip rollback` restores retained managed state without rebuilding packages or rerendering current inputs. Tracked-copy drift remains protected. Rollback is not a reversal of every command run since that generation.

## Further technical detail

[Run logs](runs.md) help diagnose a failure but are not recovery authority. The source repository's [guarantee ledger](https://github.com/gripsack-dev/gripsack/blob/{release_source}/verification/guarantees.md) records technical trust boundaries and research; release-specific verification belongs to [release notes](https://github.com/gripsack-dev/gripsack/releases), not a blanket assurance about your host.
