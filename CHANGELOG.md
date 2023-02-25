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

## [0.4.4]

### Added

 - Handle `Repl`'s in `ValueKey`
 - Allow for `IntEnum`'s in `Value.cast`
 - Added proper testing for the `torii.util.units` module.
 - Added proper testing for the `torii.util.string` module.
 - Added support for `name = ` in property checks, such as `Assert`, etc.
 - Added exports for `convert` and `convert_fragment` for rtlil, cxxrtl, and verilog into the root `torii.back` module.

### Changed

 - Updated the copyright years in the license file.
 - Hardened the RTLIL backend against generating Yosys reserved port names.
 - Removed warning on `IntEnum`'s in `Cat` (meow)
 - Ensured that files are always are written with Unix `LF` line endings.
 - Renamed the `_toolchain` module to `tools`.
 - Moved the `tool_env_var` from `torii.tools` into `torii.util.string`.
 - Renamed nox session names for `flake8` and `mypy` into `lint` and `typecheck`
 - Renamed nox session names for `build_dists` and `upload_dist` into `build` and `upload`
 - Added a default help formatter for the built-in CLI stub.

### Deprecated

 - Deprecated the remote SSH builds.
 - Deprecated passing non `Elaboratable` or `Fragment` objects to `Fragment.get`.

### Removed

 - Removed `Shape` and `tuple` casts and comparisons.
 - Removed `UserValue` and associated machinery.
 - Removed default ports from `rtlil_convert` and `verilog_convert`.
 - Removed `step` from `core.Simulator` in favor of `advance`.
 - Removed support for the `AMARANTH_ENV_*` environment variables.
 - Removed the `_BuiltinYosys` proxy object and associated bits.

### Fixed

 - Fixed an issue with the `TORII_` environment variables not being recognized.
 - Fixed missing f-strings in the `cxxrtl`, `ast`, and `intel` modules.
 - Fixed an issue in the `LatticeECP5` platform that would have caused broken SystemVerilog inclusions.
 - Fixed a bunch of miscellaneous spelling things.
 - Fixed an issue where `src` attributes would be added to generated RTLIL even if the `emit_src` attribute was `False`.
 - Fixed an issue where the tracer would encounter an unknown opcode and would return None.
 - Fixed the `iec_size` utility method to behave a bit better with strange sizes.
 - Fixed the `tcl_quote` string method that would leave un-escaped `"`'s causing the TCL script to fail due to invalid syntax.
 - Fixed an issue in the `LatticeICE40` platform where the `IceStorm` toolchain environment variable was not being normalized properly.

## [0.4.3]

### Fixed

- Fixed a small issue with the newline changes that caused synthesis to fail
- Fixed up the ULPI instance to properly handle the `clk` signal and constrain it

## [0.4.2]

### Fixed

- Fixed the project URLs for the documentation and package.
- Fixed some minor issues in the install documentation.
- Fixed the line endings on generated *nix build scripts.
- Fixed an issue where the built-in test harness was broken with writing VCDs.

## [0.4.1]

### Fixed

- Fixed issue with `invoke_tool` not emitting the environment variable properly

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


[unreleased]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.4...main
[0.4.4]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-fork...v0.4.0
[0.3.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.3...amaranth-fork
[0.1.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.1...amaranth-fork
