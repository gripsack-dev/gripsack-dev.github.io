# Source builder retired

The BuildKit source-recipe backend and OCI container-image authoring/export surface are retired in the 0.51 product line. This URL remains available for older links; it is not an installation or build guide for a supported backend. Historical release notes describe their original releases, not current capabilities.

## Source builds

Use native provider [packages](packages.md) and [environments](environments.md). Source compilation and image construction belong in your external build workflow; the retired recipe declarations and builder commands are not compatibility aliases.

## OCI images

To run an existing, digest-pinned image, use [Docker Engine services](services.md). Gripsack does not build that image. To transfer retained native package content, use [native artifact sharing](sharing.md): its OCI transport is not a runnable container image.

## Prerequisites

Native packages, dotfiles and tasks do not require Docker. Services require access to a local Linux Docker Engine. See the [services prerequisites](services.md#prerequisites).

## Worker lifecycle and limits

There is no current Gripsack builder worker or builder cache-clean operation. Do not remove historical state or database volumes as part of migrating documentation or configuration. Service volumes have their own lifecycle and are not profile rollback data.
