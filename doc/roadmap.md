# Roadmap

Where gripsack is going. 0.1 proves the spine; 1.0 is the north star —
*a misconfiguration in any file gripsack touches should produce the same
quality of error as a typo in a module.*

## Now — 0.1

- The core flow: `apply` / `plan` / `generations` / `rollback`
- `file` + `tarball` fetchers, `owned` + `tracked-copy` ownership
- Python frontend (typed, doctest-enforced), TypeScript frontend
  (typed; eval lands in 0.2)
- Generations on disk, atomic flip, no-op satisfaction
- Run logs with causal spans; the agent debug skill

## Next — 0.2

- `github_release` / `git` fetchers; the fetcher plugin host
  (`gripfetch-*` protocol live)
- TypeScript eval path
- Activation adapters (`SystemdUser` first), `merge` + `template`
  ownership
- Parallel scheduler with resource locks (the DAG already exists;
  execution is sequential today)
- Lockfile write path (`locks/<host>.lock` fully enforced)

## Later — 0.3+

- `grip adopt` (import existing configs into modules)
- Store sync between machines
- Editions & deprecation warnings (the W-code channel exists)
- Secrets (age/sops at activation)

## North star — 1.0

- **The LSP**: sema passes + config parser + validator plugins all emit
  the same span-labeled diagnostics; the editor shim maps them in.
  Editing your kitty config in VSCode and getting an error squiggle at
  the exact line — that moment.
- **Validator plugins** (`grip check`): validators for any dotfile
  format, same protocol as fetchers.
- **Fetcher registry**: `gripfetch-*` plugins for the long tail, under
  `gripsack-dev` and beyond.
