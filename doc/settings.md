# Settings

Workspace declarations live in `gripsack.ts`. Optional `env.toml` settings control source capture and operational policy; user defaults live in `~/.config/gripsack/config.toml`. Configuration is data read before workspace evaluation, not a result of authoring code.

## The frontend

The core embeds its matching TypeScript frontend and provisions a pinned Deno runtime. Evaluation has restricted captured-source reads and no environment, network or subprocess grants. Native fetching, build commands and explicit host execution have separate authority.

An installed `node_modules/@gripsack/core` selects the repository frontend unless explicitly excluded. Use a matching SDK when deliberately pinning it. `grip doctor` checks the installed package, not just a declared package version range.

For editor types without selecting a separate runtime frontend:

```toml
[capture]
exclude = ["node_modules/@gripsack/core"]
```

This literal exclusion disables that runtime pin before dereference. A glob cannot carve files out of an admitted SDK root. If `node_modules` itself is symlinked, use real ancestry or exclude that whole parent deliberately. Frontend changes can require a lock refresh and renewed source approval.

## Source capture

Captured content, including untracked and Git-ignored files, participates in approval unless explicitly excluded. `.gitignore` is not a source authority policy.

```toml
[capture]
exclude = [".venv", "**/__pycache__", ".ruff_cache/**"]
```

Literal entries exclude normalized relative subtrees. Globs support `*` within a component, `?` for one character and whole-component `**` across components. They are case-sensitive and bounded. Absolute paths, parent traversal and `~` are not valid shortcuts.

Required configuration, entrypoints, lock authority and admitted SDK roots are protected. Prefix-scoped globs require real, unaliased ancestry; use a leading suffix glob such as `**/__pycache__` for aliased content trees where appropriate. Exclusions never grant access to excluded files.

`repoTree` selection is separate: its `include`/`exclude` prefixes are literal, not globs, and cannot bypass capture admission. Exclude an irrelevant outbound virtual-environment link at the capture boundary before evaluating tree declarations.

## Review the whole capture

```sh
grip trust inspect --json
grip trust add
```

Interactive `trust add` shows the capture and policy before asking for approval. Review actual changed content as well as inventory paths. `--focus PREFIX` narrows the displayed changed-path list only: approval still binds the exact whole bundle and policy, and JSON stays complete. An out-of-focus change requires renewed approval too.

For noninteractive execution, compare separately reviewed expected digests before approval; see [unattended approval](safety.md#unattended-approval).

## State, temporary files and storage

`GRIPSACK_HOME` selects the private state root; otherwise it is `$XDG_DATA_HOME/gripsack` or `~/.local/share/gripsack`. Keep its store, trust records, journals and generations private and intact. Moving state or the installed core can invalidate managed launcher bindings.

Temporary extraction and materialization can use `TMPDIR`, `TMP` or `TEMP`. Native publication stages and seals content before final rename; a cross-filesystem transfer uses a bounded copy into destination-filesystem staging before publication. Scratch cleanup is not a substitute for publication or recovery authority.

External tools retain their own temporary-storage rules. Configure enough space for source archives, expanded trees, build cache and retained generations; `grip gc --dry-run` previews native reclamation, while `grip builder cache-clean` concerns the owned worker cache.

## Network and acquisition policy

The native fetcher honors system CA roots, `SSL_CERT_FILE`, `HTTPS_PROXY` and `NO_PROXY`. Set these in the calling environment when needed. GitHub credentials remain explicitly host-bound; see [sources](fetchers.md#authentication).

Acquisition has its own concurrency and resource budgets. Defaults are two concurrent payloads, 512 MiB downloaded, 4 GiB expanded, 100,000 entries and a 128 MiB decoder budget per payload. Downloads use disk spools rather than payload-sized RAM buffers. Limits are positive; exceeding one fails rather than truncating a package.

The [settings reference](settings/reference.md) lists values and precedence. Build worker CPU, memory and deadline flags are separate from acquisition policy; see [BuildKit](builds.md#worker-lifecycle-and-limits).
