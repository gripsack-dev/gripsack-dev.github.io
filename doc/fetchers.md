# Sources and locks

A source describes where package or recipe input bytes come from. A provider package wraps the source directly; a recipe transforms source into a new output. Source resolution and personal deployment are separate operations.

## Choose an input

| Source | Use | Frozen identity |
|---|---|---|
| `fileFetch(path)` | Captured local payload or source directory | Captured content |
| `tarball(url, sha256)` | An explicitly pinned HTTP archive | Declared SHA-256 |
| `git(url, rev?)` | A source repository, optionally selecting a revision | Resolved commit |
| `githubRelease({ repo, asset, version? })` | A release asset | Resolved release and verified asset hash |
| `conda.environment(...)` | One coherent native Conda solve | Complete selected archive closure and policy |
| `pixi.fromLock(...)` | An explicit captured manifest/lock import | Selected external locked environment |

Use [packages](packages.md) for a complete archive example, [environments](environments.md) for Conda and Pixi declarations, and [BuildKit](builds.md) for source recipes. Platform support is Linux x86_64 and WSL2, not every platform represented by upstream metadata.

`git` without a revision follows the default branch during update; a named branch or tag is then frozen to its resolved commit. An explicit commit remains fixed. A GitHub `version` selects an exact tag. Source declarations do not make arbitrary upstream payloads trustworthy.

## Update deliberately

```sh
grip update --check
grip update
```

`--check` surveys without publishing sources or writing `gripsack.lock`. Exit 0 means complete/current, 1 means complete with changes, and 2 means incomplete or operational failure. Network access, evaluator provisioning and run logging can still occur.

`grip update` resolves and verifies sources, records complete platform-keyed pins and captures frontend/import identities. It does not run build recipes or activation hooks, and it does not deploy destinations. Review the lock diff and renew exact source/policy approval when required before the next frozen consumer.

A changed Pixi manifest or lock must be imported explicitly with `grip update`; that operation does not re-solve or rewrite the external lock. Use your Pixi workflow first when you intend to change packages.

## Asset selection

GitHub asset patterns support explicit placeholders such as `{version}`, `{version.bare}`, `{system}`, `{target}`, `{arch}`, `{arch.go}`, `{arch.x64}` and `{os}`. `version.bare` removes one leading lowercase `v`; the lock keeps the actual tag. Direct archive URLs can use platform placeholders, not a version they have not resolved.

Package command and artifact selectors are literal. For a single versioned archive directory, declare `archiveRoot: { kind: "single_directory" }` and use root-relative selectors instead of repeating that version. See [package roots](packages.md#roots-and-layouts).

## Authentication

Credentials are explicitly host-bound. `GITHUB_TOKEN` takes precedence over `GH_TOKEN` and goes only to github.com/api.github.com. Enterprise credentials use `GITHUB_ENTERPRISE_TOKEN`, then `GH_ENTERPRISE_TOKEN`, with `GH_HOST` or `GITHUB_HOST` naming the intended enterprise host.

A source's `base_url` selects a destination; it is not a token grant. Cross-host and HTTPS-to-HTTP redirects do not forward authorization. Supply secrets through the trusted calling environment, not captured TypeScript; non-interactive SSH may not load your shell profile. Gripsack does not read gh's credential store or source profiles to compensate.

API quotas can be shared by an egress IP. Local pacing cannot restore upstream quota. Review rate/authentication diagnostics rather than treating every 403 as a retryable outage. Corporate certificates and proxy settings are covered in [settings](settings.md).

## Verification and resource bounds

Downloads are hashed into private disk spools and verified before extraction/publication. Archive path safety, expansion size, entry count and decoder memory limits remain enforced; a hash match does not waive them. Failed acquisition does not publish a partial package.

First-party HTTP requests use bounded retries for classified transient failures. Authentication, certificate, checksum, invalid metadata and unsafe-archive errors are not blindly retried. See the [settings reference](settings/reference.md) for acquisition budgets and [safety](safety.md) for trusted native execution.
