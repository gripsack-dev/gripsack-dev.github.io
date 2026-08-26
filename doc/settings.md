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
> config surface; [settings reference](settings-reference.md) has every
> key in table form.

## A minimal env.toml

```toml
[env]
name = "tarek"
frontend = "python"      # or "typescript"
```

That's enough for a working repo. Everything else is optional.

## Choosing a frontend

Modules can be written in Python or TypeScript — same ideas, same IR,
same tool. Pick per repo, declare it once:

```toml
[env]
frontend = "typescript"
```

- **Python** needs `python3` ≥ 3.10 with the `gripsack` package
  (`pip install gripsack`). Great with pyright.
- **TypeScript** needs `node` ≥ 18 (or bun) with `@gripsack/core`.
  Great with tsc.

One repo = one frontend. Mixed-language graphs are deliberately not a
thing; different repos may use different frontends. `grip doctor` checks
the runtime your choice needs.

## Giving your repo extra skills (eval deps)

If your modules need helper libraries at evaluation time — say, a
resolver for your company's internal artifact registry — declare them
and gripsack provisions the frontend environment for you:

```toml
[eval]
deps = ["gripsack-fetcher-artifactory==1.2.0"]
```

Pinned and cached: the same spec resolves the same inputs and the
store is content-addressed, so every machine gets the same deployed
environment. Builds are not hermetic (no sandbox — that guarantee is
Nix's, honestly theirs). This is how an env repo "carries its own
skills" — clone it elsewhere and the skills come with it.

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

`~/.config/gripsack/config.toml` accepts `[settings]` and `[sources.*]`
— the same keys as `env.toml` minus `[env]` and `[eval]`. Use it for
things that shouldn't be committed: a plugin that only exists on this
machine, a lower `keep_generations` on a small disk.

When the same key is set in both files, **the repo wins** — a cloned
repo behaves identically everywhere, and your local file can only fill
gaps or add new entries. (Environment variables and CLI flags override
both, for one-off overrides.)
