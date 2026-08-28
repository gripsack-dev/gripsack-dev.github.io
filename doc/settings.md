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

> Heads up: gripsack is pre-alpha. The schema below is stable, but some
> keys are wired up only as `grip apply` lands. This page documents the
> config surface; [settings reference](settings/reference.md) has every
> key in table form.

## A minimal env.toml

```toml
[env]
name = "tarek"
```

That's enough for a working repo. Everything else is optional.

## The frontend

Modules are TypeScript — `modules/*.ts` and `hosts/*.ts` *are* the
frontend, and there is nothing to declare. (A stale
`frontend = "python"` from older releases fails with a migration
hint; the key is gone.)

Eval runs sandboxed under a pinned Deno — no env vars, no network, no
subprocesses — and the runtime provisions itself: the first eval
downloads it once (sha256-verified, ~40MB, cached; 2.9.6 today),
`grip doctor` checks it, and `GRIPSACK_DENO` points at your own. Eval
platforms: glibc Linux and macOS — Deno ships no musl build.

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

## Machine-local config

`~/.config/gripsack/config.toml` accepts `[settings]` and `[fetchers.*]`
— the same keys as `env.toml` minus `[env]` and `[eval]`. Use it for
things that shouldn't be committed: a plugin that only exists on this
machine, a lower `keep_generations` on a small disk.

When the same key is set in both files, **the repo wins** — a cloned
repo behaves identically everywhere, and your local file can only fill
gaps or add new entries. (Environment variables and CLI flags override
both, for one-off overrides.)
