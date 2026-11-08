# Source builder retired

The BuildKit source-recipe backend and OCI image export were retired in 0.51. This page exists so old links still land somewhere useful.

- To run an existing, digest-pinned image, use [Docker Engine services](services.md). Gripsack does not build images.
- To get a tool from a release archive, Conda or a Pixi lock, use [packages](packages.md) and [environments](environments.md).
- To move retained package content to another machine or a registry, use [sharing](sharing.md); its OCI transport is not a runnable container image.

Native packages, dotfiles and tasks do not require Docker.
