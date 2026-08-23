# Writing modules

A module is the unit of your environment: how to get a tool, build it,
where its files and configs live. Two authoring styles, same IR.

## Data style (most modules)

```python
from gripsack import module, github_release, symlink, tracked_copy

module(
    "helix",
    fetch=github_release(
        repo="helix-editor/helix",
        asset="helix-{version}-x86_64-linux.tar.xz",
    ),
    install={"bin/hx": symlink("~/.local/bin/hx")},
    config={"config.toml": tracked_copy("~/.config/helix/config.toml")},
)
```

The core expands the fields into the conventional pipeline:
`fetch → build → install → config → verify → activate`.

## Class style (full control)

```python
from gripsack import Module, fetch_step, shell_step, install_step, file_fetch, symlink

class Patched(Module):
    def fetch(self):
        return fetch_step(file_fetch("payloads/hello.tar.gz"))

    def build(self):
        return shell_step("patch -p1 < fix.patch", id="patch")

    def install(self):
        return install_step({"bin/hx": symlink("~/.local/bin/hx")})
```

Phase methods return a step or a list of steps; the pipeline chains
them in order — within a phase and across boundaries — so you write
`needs` only for cross-cutting edges. **Phase methods run at eval time
only**: they build data, they never run at build time.

## Ownership modes

| mode | behavior | use for |
|---|---|---|
| `symlink(...)` | store-owned, read-only | disciplined tools |
| `tracked_copy(...)` | copied; drift detected, never silently overwritten | apps that rewrite their configs |
| `merge(...)` | managed block in a shared file | `.bashrc` (0.2) |
| `template(...)` | rendered per machine | hostnames, work vs personal (0.2) |

## Steps, resources, retries

Explicit steps carry `needs` (sibling ids or `module:step`), `resources`
(named mutexes — declare them first with `resource("pixi.lock")`; a
typo fails at eval), `verify` contracts, and `retries` overrides. The
action ladder: typed primitives → `run_step` (argv as data) →
`shell_step` (last rung) → `gripfetch-*` plugins for transports.

## Dependencies

`dep("git")` is a runtime edge; `dep("rust", edge=Edge.BUILD)` is an
ephemeral build-only dependency — present while building, GC'd after.
