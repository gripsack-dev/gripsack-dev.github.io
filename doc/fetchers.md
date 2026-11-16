# Sources and locks

A source says where a package's bytes come from. `grip update` resolves sources into `gripsack.lock`; everything that runs later uses those pins and nothing else. Resolving sources and deploying files are separate steps.

## Choose an input

| Source | Use | Frozen identity |
|---|---|---|
| `fileFetch(path)` | Captured local payload or source directory | Captured content |
| `tarball(url, sha256)` | An explicitly pinned HTTP archive | Declared SHA-256 |
| `git(url, rev?)` | A source repository, optionally selecting a revision | Resolved commit |
| `githubRelease({ repo, asset, version? })` | A release asset | Resolved release and verified asset hash |
| `conda.environment(...)` | One coherent native Conda solve | Complete selected archive closure and policy |
| `pixi.fromLock(...)` | An explicit captured manifest/lock import | Selected external locked environment |

Use [packages](packages.md) for a complete archive example and [environments](environments.md) for Conda and Pixi declarations. Platform support is Linux x86_64 and WSL2, not every platform represented by upstream metadata.

`git` without a revision follows the default branch during update; a named branch or tag is then frozen to its resolved commit. An explicit commit remains fixed. A GitHub `version` selects an exact tag. Source declarations do not make arbitrary upstream payloads trustworthy.

## Update deliberately

```sh
grip update --check
grip update
```

`--check` surveys without publishing sources or writing `gripsack.lock`. Exit 0 means complete/current, 1 means complete with changes, and 2 means incomplete or operational failure. Network access, evaluator provisioning and run logging can still occur.

`grip update` resolves and verifies sources, records complete platform-keyed pins and captures frontend/import identities. It does not run activation hooks or deploy destinations. Review the lock diff and renew exact source/policy approval when required before the next frozen consumer.

A changed Pixi manifest or lock must be imported explicitly with `grip update`; that operation does not re-solve or rewrite the external lock. Use your Pixi workflow first when you intend to change packages.

## Asset selection

GitHub asset patterns support `{version}`, `{version.bare}`, `{os}`, `{arch}`, `{arch.go}`, `{arch.x64}`, `{target}` and `{system}`. `{version}` preserves the exact resolved raw tag. `{version.bare}` removes exactly one leading lowercase `v`, not an uppercase `V` or additional leading `v`s; the lock keeps the actual tag. Direct archive URLs can use platform placeholders, not a version they have not resolved.

Since core 0.55.0, package command **values**, `artifactFile` selectors and `artifactTree` include/exclude segment prefixes support those same tokens. They bind to that package's resolved/locked source, with the asset resolver's platform spellings, not a sibling's pin or a fresh upstream lookup. Omit `githubRelease.version` when you want `grip update` to advance the release: a lock-only update then advances the command and file/tree consumers without source edits. Payload selection uses the exact expanded spelling, with no asset-search fallback.

Core 0.56.0 applies the same exact expansion to typed `artifact(output, selector)` references in exec argv, command env/cwd and environment env, and to `sourcePath` selectors in package-subject checks. In 0.55 these command/environment selectors remained literal. Each reference uses its **own referenced package's** frozen source version, never the caller's or environment's version; a package-subject check uses its subject's pin.

Planning shows expanded paths in text and JSON `resolved_paths` before package or artifact realization, without fetching payloads or claiming existence. A required version missing from the referenced source, an unknown token or an unsafe expanded relative path fails with declaration provenance; filesystem binding also checks canonical containment, including cwd. Command names, literal argv/env/cwd, scripts, destinations, host/repository paths, input names and writable staging selectors do not expand these tokens. A typed artifact reference inside argv is not a literal argument. Retained bindings stay concrete and historical portable selectors are not reinterpreted on import.

For a single versioned archive wrapper directory, `archiveRoot: { kind: "single_directory" }` remains available; selectors are relative to the selected root. See [package roots](packages.md#roots-and-layouts) and the [bare-binary example](packages.md#locked-release-payload-paths).

## Authentication

Credentials are explicitly host-bound. `GITHUB_TOKEN` takes precedence over `GH_TOKEN` and goes only to github.com/api.github.com. Enterprise credentials use `GITHUB_ENTERPRISE_TOKEN`, then `GH_ENTERPRISE_TOKEN`, with `GH_HOST` or `GITHUB_HOST` naming the intended enterprise host.

A source's `base_url` selects a destination; it is not a token grant. Cross-host and HTTPS-to-HTTP redirects do not forward authorization. Supply secrets through the trusted calling environment, not captured TypeScript; non-interactive SSH may not load your shell profile. Gripsack does not read gh's credential store or source profiles to compensate.

API quotas can be shared by an egress IP. Local pacing cannot restore upstream quota. Review rate/authentication diagnostics rather than treating every 403 as a retryable outage. Corporate certificates and proxy settings are covered in [settings](settings.md).

## Verification and resource bounds

Downloads are hashed into private disk spools and verified before extraction/publication. Archive path safety, expansion size, entry count and decoder memory limits remain enforced; a hash match does not waive them. Failed acquisition does not publish a partial package.

First-party HTTP requests use bounded retries for classified transient failures. Authentication, certificate, checksum, invalid metadata and unsafe-archive errors are not blindly retried. See the [settings reference](settings/reference.md) for acquisition budgets and [safety](safety.md) for trusted native execution.
