# Torii-HDL

Torii is a fork of [Amaranth HDL](https://github.com/amaranth-lang) that has been modified for use at [Shrine Maiden Heavy Industries](https://shrine-maiden-heavy.industries/). It has merged several of the components that were separate into a single package, and also adds new functionality, as well as some internal changes for better integration into tooling.

The evaluation board definitions have also been migrated and are located in the [torii-boards](https://github.com/shrine-maiden-heavy-industries/torii-boards) repository.


## Introduction

Please see the [Torii Introduction](https://shrine-maiden-heavy-industries.github.io/torii-hdl/intro.html) on the [online documentation](https://shrine-maiden-heavy-industries.github.io/torii-hdl/)


## Installation

Please see the [installation instructions](https://shrine-maiden-heavy-industries.github.io/torii-hdl/install.html) on the [online documentation](https://shrine-maiden-heavy-industries.github.io/torii-hdl/)

## Supported devices

Torii can be used to target any FPGA or ASIC process that accepts behavioral Verilog-2001 as input. It also offers extended support for many FPGA families, providing toolchain integration, abstractions for device-specific primitives, and more. Specifically:

  * Lattice iCE40 (toolchains: **Yosys+nextpnr**, LSE-iCECube2, Synplify-iCECube2);
  * Lattice MachXO2 (toolchains: Diamond);
  * Lattice MachXO3L (toolchains: Diamond);
  * Lattice ECP5 (toolchains: **Yosys+nextpnr**, Diamond);
  * Xilinx Spartan 3A (toolchains: ISE);
  * Xilinx Spartan 6 (toolchains: ISE);
  * Xilinx 7-series (toolchains: Vivado);
  * Xilinx UltraScale (toolchains: Vivado);
  * Intel (toolchains: Quartus);
  * Quicklogic EOS S3 (toolchains: **Yosys+VPR**).

FOSS toolchains are listed in **bold**.


## License

Torii is released under the [BSD-2-Clause](https://spdx.org/licenses/BSD-2-Clause.html), the full text of which can be found in the [LICENSE](LICENSE) file.
