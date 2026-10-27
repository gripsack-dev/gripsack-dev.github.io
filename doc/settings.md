# Settings

gripsack is configured with plain TOML in two files, and that's the
whole story:

- **`env.toml`** — lives in your env repo, committed. It makes the repo
  self-describing: any machine that clones it knows how to evaluate it.
- **`~/.config/gripsack/config.toml`** — lives on one machine, never
  committed. For machine-local things you don't want in git.

If you only remember one rule: **configuration is data, and it is read
before any of your module code runs.** Settings can never depend on what
a module computes — so there's no bootstrap paradox, ever.

This page covers current configuration. The
[settings reference](settings/reference.md) lists keys and precedence.

## A minimal env.toml

```toml
[env]
name = "tarek"
```

That's enough for a working repo. Everything else is optional.

## The frontend

New declarations use a `gripsack.ts` workspace. Legacy `modules/*.ts` and
`hosts/*.ts` remain supported for migration; both use the same sandboxed
TypeScript frontend. A stale `frontend = "python"` key is refused with
migration guidance.

Eval runs sandboxed under a pinned Deno — no env vars, no network, no
subprocesses — and the runtime provisions itself: the first eval
downloads it once (sha256-verified, ~40MB, cached; 2.9.6 today),
`grip doctor` checks it, and `GRIPSACK_DENO` points at your own. Eval
platforms: glibc Linux, including WSL2's Linux environment — Deno ships no musl
build. macOS and native Windows are not supported.

The repo's installed `node_modules/@gripsack/core` shadows the embedded
frontend. `grip doctor` reads that installed package's version, not just the
range declared in `package.json`: a stale installed copy is a **MISS** even
when the declaration is current. Use the SDK archive matching your installed
core from the [release downloads](https://github.com/gripsack-dev/gripsack/releases),
or remove the shadowing copy to use the embedded frontend. A version declaration
alone does not install or upgrade the SDK.

File permission policy needs no setting. Copies/templates follow payload
executability, track content plus full mode, and preserve user chmod drift;
merge markers track their host's mode. See [ownership modes](modules.md#ownership-modes).

## Source capture and caches

Git ignore rules do not select captured source. In 0.48, explicit glob
exclusions can keep tool caches from changing approval identity:

```toml
[capture]
exclude = ["**/__pycache__", "**/.ruff_cache"]
```

This suffix-glob form works with captured internal aliases when evaluation
uses the embedded frontend. A global glob that could carve a repository-pinned
SDK is refused. If the local SDK is only for your editor, add the literal
`"node_modules/@gripsack/core"` exclusion to select the embedded frontend
explicitly; otherwise scope cache rules to unaliased content subtrees outside
the pin root. Prefix-scoped globs must not span symlinked ancestors.

Creating/removing matching caches below existing captured directories preserves
approval. New ordinary directories, captured bytes/modes and policy changes
still require review. Literal exclusions retain their historical
appearance/removal behavior. [Full capture contract](settings/reference.md#capture-envtoml-only).

## Build-time environment

```toml
[eval.env]
CARGO_NET_GIT_FETCH_WITH_CLI = "true"
```

Injected into the apply process for the run's duration — build steps,
fetchers, and plugins inherit it (`SSL_CERT_FILE` for a corporate CA
is the canonical case). The sandboxed eval itself sees no environment
at all; what your config learns about the machine arrives through the
host entrypoint's `ctx`.

## Custom sources (fetchers)

For transports built-ins can't do (mTLS, exotic protocols), point a
named source at its plugin:

```toml
[fetchers.artifactory]
plugin = "gripfetch-artifactory"
```

Usually you don't need this section at all — plugin discovery is
automatic for `gripfetch-<name>` executables on your PATH. Declare it
when you want an explicit path or a different name.

## Housekeeping

```toml
[settings]
keep_generations = 20
```

How many generations to keep before `grip gc` reclaims store paths.
Rollback depth vs disk. Default keeps everything until you gc manually.

Acquisition has its own budget, separate from module concurrency. By default,
at most two payloads acquire at once, with 512 MiB downloaded, 4 GiB expanded,
100,000 entries and a 128 MiB decoder budget per payload. Downloads use private
disk spools, not payload-sized RAM buffers. The positive integer settings
`acquisition_jobs`, `download_limit_bytes`, `expanded_limit_bytes`,
`archive_entry_limit` and `decoder_memory_bytes` are listed in the
[settings reference](settings/reference.md#settings-envtoml-or-user-config).

## Temporary files and store publication

`TMPDIR` selects ordinary temporary storage; when it is unset,
Linux normally uses `/tmp`. **The temporary directory need not be on
the same filesystem as `GRIPSACK_HOME`.** This is the core-owned
publication contract, not a requirement to put all scratch under the
store:

| operation | staging and final publication |
|---|---|
| GitHub releases and other built-in archive fetches | private download/unpack staging; checked payload published into the store |
| native `conda.environment` | helper solve scratch, archive spools/extraction and prefix staging use temporary storage; the core validates the frozen result before store publication |
| `pixi.fromLock` | parses captured manifest/lock files without running a `pixi` subprocess, then uses the same frozen archive/materialization path as native Conda |

The publisher seals and syncs staged content, then renames it. When
that rename crosses filesystems (`EXDEV`), it streams a copy into a
fresh sibling **on the destination filesystem**, preserves file
modes and symlinks, syncs the copied files/directories, then atomically
renames the completed sibling to the final name and syncs its parent.
It never exposes the partially copied tree under the final store name.
Conda's Rattler helper uses copy-only linking and patches for the final
prefix; it does not require hard links from `/tmp` into the store.

Provision sufficient space on **both** filesystems for staging and
publication. Setting `TMPDIR` to suitable private scratch is a
capacity/performance choice, not an ownership or integrity bypass.
External `pixi lock` generation, custom fetcher plugins, and arbitrary
user commands retain their own scratch/publication rules; this
guarantee does not repair their cross-device rename assumptions.

Measured with public 0.45.0 in an isolated Linux container: native
Conda and Pixi import each published 42 real frozen archives with
`TMPDIR`, `TMP` and `TEMP` unset, `/tmp` on tmpfs and the private
state/store on a different filesystem. Both apply and retained
reapply succeeded; retained store bytes, modes and directory/file
identity remained unchanged. Acquisition used local fixture HTTPS,
not external network access; materialization and retained reuse made
no requests. No `pixi` executable was on `PATH`. The external
reviewer's archive/GitHub separate-filesystem success is separate
reviewer evidence. These observations do not qualify arbitrary
filesystems or third-party commands.

## Machine-local config

`~/.config/gripsack/config.toml` accepts `[settings]` and `[fetchers.*]`
— the same keys as `env.toml` minus `[env]` and `[eval]`. Use it for
things that shouldn't be committed: a plugin that only exists on this
machine, a lower `keep_generations` on a small disk.

When the same key is set in both files, **the repo wins** — a cloned
repo behaves identically everywhere, and your local file can only fill
gaps or add new entries. (Environment variables and CLI flags override
both, for one-off overrides.)
