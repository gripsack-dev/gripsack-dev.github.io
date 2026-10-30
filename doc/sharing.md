# Native artifact sharing

`grip package` transfers passive Linux x86_64 artifacts. Import does not evaluate TypeScript, install tasks or schedules, run publisher checks or activate a profile. A signature authenticates an authorized publisher's claim; it does not prove the program is safe or universally relocatable.

## Prepare a native bundle

This minimal example deliberately depends on the receiving host's `/bin/sh`. Create `input/components/app/bin/hello`:

```sh
#!/bin/sh
printf '%s\n' 'hello from a native package'
```

Make that file executable with `chmod 755 input/components/app/bin/hello`. Create `specification.json`:

```json
{
  "version": 1,
  "namespace": "example/tools",
  "publisher": "example",
  "target": {
    "os": "linux", "arch": "x86_64", "abi": {"kind": "linux"},
    "minimum_kernel": "3.2", "cpu": "x86_64"
  },
  "layout": {
    "kind": "relocatable",
    "contract": {
      "behavior": "Shell script requiring recipient /bin/sh, with no producer-prefix dependencies"
    }
  },
  "components": [{
    "id": "app", "payload": null, "tree": null, "runtime": [],
    "conda": null, "external": null, "inventory": []
  }],
  "roots": ["app"],
  "commands": {"hello": {"component": "app", "executable": "bin/hello", "args": []}},
  "environment": {},
  "licenses": [],
  "redistribution_authorized": true
}
```

Only authorize redistribution for content you have the right to distribute. Include required notices and list their aggregate-relative paths in `licenses` for real packages. The packer captures bounded trees and fills exact payload, tree, path and mode inventories.

Provide your publisher's explicitly selected **raw 32-byte Ed25519 seed**, owned by your UID with mode `0600`; PEM or a password is not the key format. Keep it outside captured source and package metadata. Configure recipient trust independently before importing:

```sh
grip package pack --manifest specification.json --source input \
  --output bundle --key /private/publisher-seed.bin --key-id publisher-2026
grip package import --bundle bundle
```

These paths identify an operator-provided key, not a downloadable example secret. The resulting bundle directory contains `manifest.json`, `envelope.json`, deduplicated `blobs/<sha256>` and, when needed, independent dependencies under `manifests/<digest>/`.

## Recipient trust

The recipient configures `$GRIPSACK_HOME/sharing/trust.json` with the actual publisher's base64-encoded raw 32-byte public key:

```json
{
  "version": 1,
  "keys": [{
    "key_id": "publisher-2026",
    "publisher": "example",
    "namespaces": ["example/tools"],
    "public_key": "BASE64_RAW_32_BYTE_ED25519_PUBLIC_KEY",
    "allowed_layouts": ["relocatable"],
    "required_validators": ["manifest-integrity", "payload-integrity", "layout-safety"]
  }],
  "revoked_keys": [],
  "revoked_manifests": []
}
```

Replace the public-key marker with a separately authenticated value; it is not executable sample trust. There is no trust-on-first-use. Namespaces are exact, not wildcards. Key removal, key or manifest revocation and tightened validator/layout policy block subsequent managed consumption; they do not kill running processes or delete retained bytes. Offline validation cannot discover unseen remote revocations. Independent execution of extracted files is outside subsequent Gripsack enforcement.

## Inspect and select

Use the actual canonical package manifest SHA-256 reported by the package operation, not the registry transport digest:

```sh
: "${manifest:?set the package manifest SHA-256}"
grip package inspect --manifest "$manifest"
grip package export --manifest "$manifest" --output exported-bundle
```

Package commands emit JSON. A recipient-authored workspace selects the imported content with `source.package({ manifest: "ACTUAL_PACKAGE_MANIFEST_SHA256" })` as its package provider. For the example, its exported command path is `components/app/bin/hello`. Recipient-owned package, environment, profile and task declarations decide exposure and checks; import alone grants no automation authority.

## OCI transport is not Docker runtime

```sh
: "${registry:?set the HTTPS registry URL}"
: "${repository:?set the registry repository name}"
grip package push --manifest "$manifest" \
  --registry "$registry" --repository "$repository" --reference release
: "${transport_digest:?set sha256: followed by the reported OCI transport digest}"
grip package pull --digest "$transport_digest" \
  --registry "$registry" --repository "$repository"
```

Push publishes blobs before the OCI artifact manifest. Pull is digest-only; a mutable tag is discovery, not a frozen selection. Registry authentication is explicit through `--bearer-token-file` or `--basic-credentials-file` (private mode `0600` JSON containing `username` and `password`). HTTPS uses rustls. There is no redirect, implicit authentication-challenge discovery, retry or fallback. Anonymous local test registries require explicit `--insecure-loopback` for HTTP.

This OCI artifact is **not a runnable container image** and needs no Docker Engine or BuildKit worker. [Services](services.md) separately run existing Docker images. The [source builder](builds.md) is retired. Relocation is a declared runtime contract, not general embedded-prefix rewriting; validate actual recipient execution and host requirements before relying on a shared package.

## Targets and independent dependencies

Targets contain admitted OS, architecture, minimum kernel, CPU and ABI requirements, not free-form compatibility claims. A glibc target uses `abi: { "kind": "glibc", "minimum": "2.28" }`; the Linux ABI target above does not grant arbitrary host libraries. Import and managed consumption measure the actual receiving host. The example's `/bin/sh` prerequisite still needs separate operator qualification.

A component can instead reference an already-imported independently signed package through `external: { manifest, namespace, publisher }`, with null local payload/tree/Conda fields. Packing includes the complete signed dependency closure. Every independent manifest needs its own namespace-scoped publisher authorization; the root signature cannot authorize another publisher. Independent manifest references must form an acyclic graph. Missing metadata or payloads fail offline without registry fallback. A relocatable aggregate cannot embed Conda or fixed prefixes and relabel them relocatable.

## Passive mixed environments

The signed `layout: { "kind": "environment" }` selects ordered native, Conda archive-set and independent package roots. Its `commands` map binds exported names to component-relative executables and fixed arguments. It does not copy a producer's installed prefix.

Environment values use typed literal or artifact bindings, such as `{ "kind": "literal", "value": "development" }` or `{ "kind": "artifact", "output": "python", "selector": "." }`. Artifact selectors resolve against the recipient's admitted component. Host paths, repository inputs, command/effect references and reserved loader/interpreter/shell-control variables are rejected; command PATH comes from selected typed commands.

For an imported environment, select `source.package({ manifest: digest })` with package `layout: { kind: "prefix_materialized" }` and command paths `bin/<exported-name>`. This differs from the relocatable tree example's `components/app/bin/hello` path. Recipient-owned declarations grant exposure and invocation; passive import sets no shell variables, runs nothing and activates no profile.

## Conda and wheel reconstruction

Conda sharing transfers a single archive-set component with the admitted lock, original archives, core-approved pinned helper and required signed/pinned redistribution notices, not a copied installed prefix. Import reconstructs at the recipient's actual final prefix and records that realization separately. Missing originals or helper fail offline without solving, repodata access or a network fallback.

Binary prefix replacement is limited by the placeholders in the original Conda archives. An excessively long final store prefix is rejected, not truncated or silently redirected. Use a shorter `GRIPSACK_HOME` when necessary; arbitrary prefix lengths are not a relocation guarantee.

Supported explicitly hash-pinned wheels can accompany the Conda environment, including supported wheel records selected from an imported Pixi lock. The maintained UV installer runs offline inside the core-pinned helper; core validation binds installed bytes, generated console entrypoints and receipts to original wheels and the final prefix. This does not run pip, resolve missing Python dependencies, compile bytecode or execute package-provided installers. See [wheel authoring and limits](environments.md#hash-pinned-python-wheels).

Unsupported selected Pixi build/resolution policies or wheel records are errors, not silently omitted packages. Runtime compatibility and actual consumer behavior still require recipient qualification; this guide does not claim a completed offline reconstruction test.

The [selected core sharing reference](https://github.com/gripsack-dev/gripsack/blob/{release_source}/README.md#share-native-packages-without-activating-profiles), [package-sharing fixture](https://github.com/gripsack-dev/gripsack/blob/{release_source}/e2e/test_package_sharing.py) and [offline Conda fixture](https://github.com/gripsack-dev/gripsack/blob/{release_source}/e2e/test_package_conda_offline.py) provide the source contract and runnable coverage definitions, not evidence that those checks ran for this site.
