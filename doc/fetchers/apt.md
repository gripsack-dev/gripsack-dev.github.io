# apt (fetcher plugin)

Distro packages as gripsack modules. `gripfetch-apt` wraps the **host's**
apt — never bundles or reimplements it — so an enterprise machine's
internal mirrors (`/etc/apt/sources.list.d`) just work, and proxy env
is honored the way the host already does it.

## Install

Declarative — the plugin lifecycle provisions it from the release:

```toml
# env.toml
[fetchers.apt]
package = "gripsack-dev/gripfetch-apt@0.1.0"
```

The first `grip check`/`apply` downloads the binary for your platform,
verifies it against the release's sha256 sidecar, receipts it into the
plugin store, and prints where it came from. No PATH editing; the
store wins over PATH. For development, `path = "/opt/bin/gripfetch-apt"`
overrides. (Or: `cargo install gripfetch-apt` and it's on PATH.)

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
- **The payload layout**: `usr/bin/*` maps to `bin/*`, so modules
  install with the usual `install={"bin/jq": ...}` shape.
- **Enterprise mirrors**: your sources.list is the truth; rate budgets
  are the fetcher's to declare (apt declares none — mirrors aren't APIs).

## Notes

- Version strings are the distro's, build suffixes included
  (`2.10-3build1` — they differ across distros; resolve once with
  `grip update` and the lockfile keeps everyone honest).
- The fetcher fails loudly when apt is absent, when a pinned version
  left the mirror, and on hash mismatches — never a silent payload.
- `.deb` extraction guards path traversal (no `../`, no absolute
  paths) before anything is staged.

## The fetcher itself

[gripfetch-apt](https://github.com/gripsack-dev/gripfetch-apt) — Rust,
single static binary, 9/9 against
[gripfetch-conformance](https://github.com/gripsack-dev/gripfetch-conformance),
crates.io `gripfetch-apt`. Writing your own transport? Its source plus
the suite are the worked example.
