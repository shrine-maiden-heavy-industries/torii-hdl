# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Unreleased template stuff

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
-->

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.4.2]

### Fixed

- Fixed the project URLs for the documentation and package.
- Fixed some minor issues in the install documentation.
- Fixed the line endings on generated *nix build scripts.
- Fixed an issue where the built-in test harness was broken with writing VCDs.

## [0.4.1]

### Fixed

- Fixed issue with `invoke_tool` not emitting the enviroment variable properly

## [0.4.0]

### Added

- Folded in `stdio` library components.
- Folded in `soc` library components.
- Folded in resources from [torii-boards](https://github.com/shrine-maiden-heavy-industries/torii-boards) into the `torii.platform.resources` module.
- Added [flake8](https://flake8.pycqa.org/en/latest/) configuration file.
- Added [mypy](http://mypy-lang.org/) configuration file.
- Added [Code Of Conduct](https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CODE_OF_CONDUCT.md).
- Added a `noxfile.py` for use with [nox](https://nox.thea.codes/en/stable/).
- Added an updated python unittest wrapper for use with Torii.
- Added string utility module.
- Added units utility module.
- Added dependency `rich`.
- Added `CANResource` to `torii.platform.resources.interface`.
- Added `ice40warmboot` to `torii.lib.vendor.lattice.ice40`.
- Added empty `torii.lib.vendor.xilinx` module.
- Added `VGADACResource` to `torii.platform.resources.display`.
- Added preliminary support for the yosys+nextpnr-xilinx flow on the Xilinx platform.
- Added [Changelog](https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CHANGELOG.md) file.
- Added `QSPIFlashResource` to `torii.platform.resources.memory`.
- Added `JTAGResource` to `torii.platform.resources.interface`.
- Added `EthernetResource` to `torii.platform.resources.interface`.

### Changed

- Refactored the [documentation](https://shrine-maiden-heavy-industries.github.io/torii-hdl/).
- Migrated string escape functions from the `TemplatedPlatform` into the new strings utility module.
- Moved `log2_int` and `bits_for` into the new units utility module.
- Moved vendor modules into `torii.platform.vendor`.
- Replaced deprecated `abstractproperties` with `property`/`abstractmethod` combo.
- Moved the `tracer` module into `torii.util`.
- Moved the `_unused` module into `torii.hdl`.

### Removed

- Removed the `nMigen` compatibility layer.
- Removed the `migen` compatibility layer.
- Removed the compatibility tests.
- Removed the RPC server.
- Removed the old FHDL test case.
- Removed the `tuple` case from `Shape`.
- Removed the warning from `rtlil.convert` and `verilog.convert` about implicit ports.
- Removed the `_ignore_deprecated` decorator.
- Removed the `C` alias for `Const`.

### Fixed

- Fixed the package name.
- Fixed the package authors.
- Fixed the package trove classifiers.
- Fixed all flake8 warnings on the entire codebase.
- Fixed indentation.
- Fixed docstring formatting.

## [0.1.0] - [0.3.0]

No changelog is provided for these versions as they are all older tagged releases of [Amaranth](https://github.com/amaranth-lang/amaranth) from before the fork.


[unreleased]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.2...main
[0.4.2]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-fork...v0.4.0
[0.3.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.3...amaranth-fork
[0.1.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.1...amaranth-fork
