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


## [0.7.1]

### Fixed

  - Fixed a bug with typing asserts that caused resource unwinding to fail on differential pairs.

## [0.7.0]

### Added

 - Added new `torii.platform.formal.FormalPlatform` for formal verification of Torii designs.
 - Added [formal platform examples](https://github.com/shrine-maiden-heavy-industries/torii-hdl/tree/main/examples/formal)
 - Added `Value.inc()` and `Value.dec()` calls to help deal with the `sig.eq(sig + 1)` pattern that is all too common.
 - Added explicit mention of Python 3.13 support.
 - Added `structured records` to allow for ease of typing `torii.hdl.rec.Record`'s


### Changed

 - Torii `Elaboratable`'s now have a new optional `formal` function for use in formal verification with the Torii `FormalPlatform`.
 - Torii platforms now have `get_override_list` and `get_override_int` overrides for platform template support.
 - Torii platforms now have optional `description` and `pretty_name` properties.
 - Use of `read_ilang` has been replaced with `read_rtlil` in the Gowin platform, which was the only platform that used the deprecated Yosys command.

### Deprecated

 - Moved the contents of `torii.asserts` to `torii.lib.formal`.

### Removed

 - Removed deprecated `log2_int`
 - Removed deprecated `torii.platform.vendor.intel` Module
 - Removed deprecated parameter `run_script` from `BuildPlan.execute_local`

### Fixed

 - Fixed huge chunk of typing, lots to do but should improve useability and ergonomics.
 - Fixed a resource layout issue within the `torii.platform.resources.interface.HyperBusResource`


## [0.6.2]

### Fixed

 - Fixed a bug in the definition of the `QSPIResource` in `torii.platform.resources.memory`, again...


## [0.6.1]

### Fixed

 - Fixed a bug in the definition of the `QSPIResource` in `torii.platform.resources.memory`

## [0.6.0]

### Added

 - Rough initial type annotations to `torii.hdl.mem`
 - Added the ability to specify `tar` for the `torii.build.run.BuildPlan.archive` call.
 - Added check inside `Record`s to ensure they're properly constructed prior to accessing their fields.
 - Added the ability to override a Value's operators.
 - Added the ability to put non-signals into `write_vcd`'s `traces` parameter.
 - Added name disambiguation for traced signals where they share the same name.
 - Added `ValueLike` and `ShapeLike`, mainly for additional typing and instance checking assistance.
 - Added the ability for `Cat` and `Slice`, statements to be cast as a `Const` value.
 - Added `#!/bin/sh` to the top of build shell scripts.
 - Added `BuildPlan.extract` to extract files from the build plan without having to run it, this replaces the functionality that occurred when `BuildPlan.execute_local` was passed with `run_script = False`.
 - Added `BuildPlan.execute_docker` to allow for invoking a build inside a specified docker container.
 - Added `log2_ceil` and `log2_exact` to replace `log2_int` with the `False` and `True` params respectively.
 - `ShapeCastable` objects can now be const initialized.

### Changed

 - Improved Oscillator frequency diagnostics for `torii.vendor.GowinPlatform`.
 - Fixed `torii.lib.fifo` FIFOs to use the new memory semantics correctly.
 - `torii.lib.soc.csr` Multiplexer shadow registers have been re-designed.
 - Bumped minimum Python version from 3.9 to 3.10.
 - Renamed `IntelPlatform` to `AlteraPlatform`.
 - FWFT mode is default for all FIFOs now.
 - Bumped the minimum version of Yosys to 0.30.
 - Empty `Case` blocks now throw an exception when being used in place of a `Default` block
 - Behavioral change warning in empty `Value.matches()` where currently it returns `Const(1)` but will return `Const(0)` in the future.
 - We now only close a VCD or GTKW file in the simulator if it was opened by the simulator.
 - Build shell scripts will now be marked as executable on unix-like hosts.
 - `Instance` objects know collect source location information.
 - Memories have been turned into a first-class IR representation.
 - Out-of-range rests now error, not just warn.
 - A warning is now generated when a `Case()` falls after a `Default()`, and an error is raised when there are multiple `Default()`'s in a `Switch`
 - Shape casting a `range(1)` now resolves to an `unsigned(0)`

### Deprecated

 - Deprecated `torii.vendor.intel` and `torii.vendor.intel.IntelPlatform` in favor of `torii.vendor.altera` and `torii.vendor.altera.AlteraPlatform`.
 - Deprecated `execute_local()`'s `run_script` param in favor of `extract`
 - Deprecated use of `log2_int` in favor of `log2_ceil` and `log2_exact` where appropriate.

### Removed

 - Removed deprecated `torii.platform.vendor.lattice_*` modules.
 - Removed deprecated `Repl` call in favor of `Value.replicate`.
 - Removed `set -x` if the `verbose` param is set for platform builds.
 - Removed the last little bit of `$verilog_initial_trigger` traces.
 - Removed sub-classing of `AnyValue` and `Property`

### Fixed

 - Fixed `ToriiTestCase.settle` to handle "0" count settles.
 - Fixed `torii.hdl.dsl.Module`'s constructor to properly use `super()` rather than a parent class name call.
 - Load of typing annotation fixes.
 - Cleaned up a load of blank `asserts`, they should now have more clear error diagnostics.
 - Fixed a handful of typos throughout the library and documentation.
 - Fixed tracer calls for Python 3.13
 - Fixed `Array` not being indexable by a `ValueCastable`.
 - Fixed `ValueCastable` not being accepted as a simulation coroutine command.
 - Fixed handling of redundant `Case` branches.
 - Fixed `Value.shift_right` and `Value.as_signed` edge cases.
 - Fixed using 0-width `Switch`'s with integer keys.
 - Trying to use the Python `in` operator on a `Value` now raises a sensible error.
 - When indexing or slicing a Value with another Value, it now raises an error and suggests to use `Value.bit_select` or `Value.word_select` instead.
 - Fixed simulation look when process catches an injected exception.

## [0.5.0]

### Added

 - Added some minor comments to the `torii.sim.core` module about the function of some of the objects.
 - Added `torii.vendor.gowin.GowinPlatform`.
 - Added support for Xilinx Atrix UltraScale+ part numbers.
 - Added `env` argument to `BuildPlan.execute_local`.
 - Allowed removing `src` attributes on RTLIL output.

### Changed

 - Moved the Lattice platform defs into their own submodule `torii.platform.vendor.lattice`.
 - Replaced the `distutils.ccompiler` with the `setuptools.command.build_ext` module for `torii.tools.cxx`.
 - Disabled the warning emitted on `~True`/`~False` when using it as a value in Torii in Python versions older than 3.12.
 - Relaxed the `PyVCD` dependency version to now also include `0.5`.
 - Ensured `Value.__abs__` now returns `unsigned` `Shape`.
 - Restructured the `torii.lib.coding` module away from being a monolithic file.
 - Prohibited absolute paths in `BuildPlan.add_file`.
 - Added lowering of `Memory`'s directly to RTLIL `$mem_v2` cells.
 - Ensured `Part` offsets are always unsigned.
 - Disallowed `signed(0)` values.

### Deprecated

 - Old Lattice platform names have been deprecated in favor of the new platform location.
 - Deprecated `Repl` in favor of `Value.replicate`.

### Removed

 - Removed the `torii.cli` module
 - Removed the `remote-build` category from the `setup.py` `extra_requires` due to removal of remote builds.
### Fixed

 - Fixed an issue where the `IrDAResource` was not imported into the `torii.platform.resources` `__init__.py`
 - Fixed the `torii.utils.tracer` module to properly handle `STORE_DEREF` and `EXTENDED_ARG`s.
 - Fixed signed value normalization inside `Const`.
 - Fixed issue with `Value.rotate_left`/`Value.rotate_right` on 0-width values.
 - Fixed a semantic issue with range handling inside `Shape.cast`.
 - Fixed an off-by-one issue in the validation of `Slice`es.
 - Fixed the signedness of the resulting `Shape` when doing subtraction.
 - Fixed handling of `ValueKey.__eq__`.
 - Fixed source-location attribution for `Slice`es.
 - Fixed the order of when `Value.cast` should have been called in the `Part` and `Slice` constructors.
 - Fixed a warning on python 3.12 with the `pyrtl` simulator warning about bitwise negations on booleans.
 - Fixed a test case failure that would only occur on Windows due to it's backwards path separator.
 - Ensured `Value.cast` is inside `Part`'s and `Slice`s constructor.
 - Fixed  test case that was having issues on Windows paths.
 - Removed translation of empty subfragments as that would cause unintentional blackboxing on Vivado and Yosys.

## [0.4.5]

### Added

 - Added `-norom` and `-proc` options to verilog generation if available in Yosys.
 - Added [a small tutorial](https://torii.shmdn.link/tutorials/external_modules.html) on using `platform.add_file` with `Instance` for referencing external modules.
 - Added conversion helpers to/from picoseconds.
### Changed

 - Updated the minimum Yosys version to `0.15`.
 - Minor typing updates.
 - `Value.matches` now returns `Const(1)` when no value is supplied.
 - `Platform.build` now allows for lists of strings to be passed for argument.
 - Invocations of `read_ilang` in Yosys scripts has been replaced with `read_rtlil` as `read_ilang` has been deprecated for a while now.
 - Replaced `sim_case` in `ToriiTestCase` with `ToriiTestCase.simulation` and added two attributes for defining the simulation domain `ToriiTestCase.comb_domain` and `ToriiTestCase.sync_domain`, the latter of which takes a `domain = ` param to specify which synchronous domain it is using.
 - The default platform in `ToriiTestCase` has been replaced with `None`, rather than `MockPlatform`
 - Gated the initialization of the `ToriiTestCase` `dut` behind a check to prevent non-simulating tests, and tests that don't use the DUT from exploding.
 - Made the `connectors` property on `Platform`'s optional, it now currently defaults to an empty list.
 - Updated [rich](https://github.com/Textualize/rich) dependency version from `~=12.6.0` to `>=12.6.0`
### Deprecated

 - Deprecated the current `torii.cli.*` methods in anticipation of replacing them.
### Removed

 - Removed remote SSH build support
 - Removed `Value.__hash__`

### Fixed

 - Corrected how environment variables were extracted making them more consistent.
 - Fixed the `ToriiTestCase` so it's now properly functional
 - Clarified the usage of `Cat` in the language documentation, noting that it can take more than two arguments for concatenation.
 - Added a warning on potential off-by-one errors when invoking `Signal` with a `range` and having the reset value be the same as the end of the range.

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


[unreleased]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.7.1...main
[0.7.1]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.5...v0.5.0
[0.4.5]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-fork...v0.4.0
[0.3.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.3...amaranth-fork
[0.1.0]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/compare/amaranth-v0.1...amaranth-fork
