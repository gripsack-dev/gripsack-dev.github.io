# Installation

One static binary, `grip`, with the TypeScript frontend embedded. The separate SDK archive is optional: install it for editor types or to pin the frontend deliberately.

## Supported platforms

The supported hosts are **Linux x86_64 and WSL2's Linux environment**. Native Windows, macOS and ARM are outside the current support scope. Package ABI, libc/kernel requirements and actual runtime dependencies still need to match the receiving host.

## Install the binary

Download the [selected core release](https://github.com/gripsack-dev/gripsack/releases/tag/core-v{core_version}) into a versioned user directory:

```sh
set -eu
version={core_version}
asset="gripsack-$version-x86_64-unknown-linux-musl.tar.gz"
base="https://github.com/gripsack-dev/gripsack/releases/download/core-v$version"
work=$(mktemp -d)
curl --fail --location --proto '=https' "$base/$asset" -o "$work/$asset"
curl --fail --location --proto '=https' "$base/$asset.sha256" -o "$work/$asset.sha256"
(cd "$work" && sha256sum --check --strict "$asset.sha256")
tar -xzf "$work/$asset" -C "$work"
prefix="$HOME/.local/lib/gripsack/$version"
mkdir -p "$prefix"
test ! -e "$prefix/grip" || { echo "Refusing to replace $prefix/grip" >&2; exit 1; }
install -m755 "$work/gripsack-$version-x86_64-unknown-linux-musl/grip" "$prefix/grip"
export PATH="$prefix:$PATH"
grip --version
grip doctor
```

Keep that versioned directory on your shell's `PATH`. This leaves an existing
installation intact rather than replacing a binary used by managed launchers.

Checksums detect corruption, not tampering. The signed installer (`install.sh`) and `grip self-update` need signed release metadata; when a release ships without it, use the manual steps above.

Keep the installed path stable: profile launchers record the absolute core location and private state path. If you move the binary, restore its location or reapply profiles using the replacement installation.

## Runtime prerequisites

- **Evaluation:** the core provisions a pinned, SHA-256-verified Deno runtime when needed. First use needs download access unless that runtime is already available or deliberately supplied through `GRIPSACK_DENO`.
- **Native packages:** download access to their sources on a cold realization, suitable host ABI/runtime support, and space for verified archives and retained output. Native Conda uses the core's helper/materialization path, not a user-installed Pixi command.
- **Container services:** a usable local Linux Docker Engine and access to the digest-pinned images. See [services prerequisites](services.md#prerequisites).
- **Profiles:** write access to the selected destinations. No root or Docker service is required for ordinary file-only deployment.

## Editor support and frontend selection

Use the SDK archive matching the installed core if you want editor types or explicitly pin the frontend. An installed `node_modules/@gripsack/core` can select the repository frontend rather than the embedded one; changing it is a source/policy change, not merely editor configuration.

`grip doctor` inspects the installed package version, not just the version range in `package.json`. An editor-only SDK can be excluded from runtime source capture to select the embedded frontend explicitly; see [settings](settings.md#the-frontend).

## First workspace

Continue with [your first workspace](workspaces.md). For a native tool see [packages](packages.md); for a Conda toolchain see [environments](environments.md). Keep an independent backup of anything irreplaceable while you are getting started.
