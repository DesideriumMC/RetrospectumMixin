# Changelog

This file records notable changes to Retrospectum Mixin.
The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-11-06

### Changed

- **Breaking:** Mixin configuration discovery now uses the `MixinConfigs` manifest
  attribute. Mods that use `RetroMixinConfigs` must migrate their manifests.

### Fixed

- Abort bootstrap if the required FML remapper fails to initialize and preserve
  the original exception so the startup failure can be diagnosed.

## [0.1.0] - 2026-11-05

### Added

- Added a portable Maven repository distribution for the shaded runtime, sources,
  and Javadoc.
- Added a verified publishing workflow for the public Maven repository.

## [0.1.0-alpha.1] - 2026-11-03

### Added

- Introduced a shared Mixin 0.8.7 bootstrap for Minecraft Forge 1.6.4
  (9.11.1.1345) on Java 7 and 8, supporting clients and dedicated servers.
- Added Mixin configuration discovery through the `RetroMixinConfigs` manifest
  attribute and the `retromixin.mixin.configs` development property.

[Unreleased]: https://github.com/DesideriumMC/RetrospectumMixin/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DesideriumMC/RetrospectumMixin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DesideriumMC/RetrospectumMixin/compare/v0.1.0-alpha.1...v0.1.0
[0.1.0-alpha.1]: https://github.com/DesideriumMC/RetrospectumMixin/releases/tag/v0.1.0-alpha.1
