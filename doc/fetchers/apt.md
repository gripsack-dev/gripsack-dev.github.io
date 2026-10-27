# apt (fetcher plugin)

An external fetcher for the **supported legacy host/module API**.
`gripfetch-apt` wraps the host's `apt-cache` and `apt-get download`;
it does not install system packages or run maintainer scripts.
Configured mirrors and proxy settings remain host inputs.

For new IR8 workspaces, start with the
[0.48 provider/package APIs](https://github.com/gripsack-dev/gripsack/blob/core-v0.48.0/typescript/README.md#a-workspace-is-a-function-ir-v8).
The legacy `pluginFetch` example below is not a workspace provider
adapter. Core 0.48 supports Linux/WSL2 x86_64; this plugin additionally
requires an apt-equipped host and suitable package indexes.

## Install

Declarative — the plugin lifecycle provisions it from the release:

```toml
# env.toml
[fetchers.apt]
package = "gripsack-dev/gripfetch-apt@0.1.0"
```

When the registered plugin is needed, core provisions its release
binary and verifies the mandatory SHA-256 sidecar before storing it.
This is checksum verification, not signature authentication or a
sandbox. For a separately installed development binary, use
`path = "/opt/bin/gripfetch-apt"` **instead of** `package`.
Do not rely on unregistered PATH discovery.

## Use

<div class="window">
  <div class="titlebar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="wtitle">a module fetching from apt</span></div>
<pre><code class="language-typescript">import { module, pluginFetch, symlink, verifyBinary } from "@gripsack/core";

export default module("jq", {
  fetch: pluginFetch("apt", { package: "jq", version: "1.7.1-3build1" }),
  install: { "bin/jq": symlink("~/.local/bin/jq") },
  verify: verifyBinary("bin/jq", ["--version"]),
});</code></pre>
</div>

## What works

- **Pinned and unpinned**: omit `version` to resolve the newest the
  host's mirrors serve (the pin lands in `grip update`'s lockfile);
  pin it to reproduce exactly — a re-fetch stages the payload and
  verifies its canonical tree hash against the lock.
- **No root**: `apt-get download` needs none.
- **The payload layout**: `usr/bin/*` maps to `bin/*`, so legacy modules
  use `install: { "bin/jq": symlink(...) }`.
- **Enterprise mirrors**: your sources.list is the truth; rate budgets
  are the fetcher's to declare (apt declares none — mirrors aren't APIs).

## Notes

- Version strings are the distro's, build suffixes included
  (`2.10-3build1` — they differ across distros; resolve once with
  `grip update` and the lockfile keeps everyone honest).
- The fetcher fails loudly when apt is absent, when a pinned version
  left the mirror, and on hash mismatches — never a silent payload.
- `.deb` extraction rejects archive paths that escape staging. The
  native plugin still runs with your privileges.
- Downloading one `.deb` does not resolve or retain a complete dependency
  closure. A binary can still require host libraries; this is not
  portable or sealed workspace-package execution.
- The plugin reports `W02` when the package index has no SHA-256.
  The retained canonical-tree pin still checks locked reproduction;
  it does not authenticate an unreviewed first download.

## The fetcher itself

[gripfetch-apt](https://github.com/gripsack-dev/gripfetch-apt) is a
separate Rust plugin. Its README reports **9/9 protocol conformance**
against [gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance);
that is the plugin's historical report, not a fresh 0.48 integration
qualification or proof for every mirror and distro. Consult its release
assets for availability. This is separate from core 0.48, which is
installed manually from its unsigned release archives and has no
npm/crates.io publication.
