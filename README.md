# Torii-HDL

Torii is a fork of [Amaranth HDL] that has been modified for use at [Shrine Maiden Heavy Industries]. It has merged several of the components that were separate into a single package, and also adds new functionality, as well as some internal changes for better integration into tooling.

The evaluation board definitions have also been migrated and are located in the [torii-boards] repository.

There is also a list of [projects using Torii] that are using Torii, and we'd love to add yours too!

## Introduction

Please see the [Torii Introduction] on the [online documentation].

## Installation

Please see the [installation instructions] on the [online documentation].

## Supported devices

Torii can be used to target any FPGA or ASIC process that accepts behavioral Verilog-2001 as input. It also offers extended support for many FPGA families, providing toolchain integration, abstractions for device-specific primitives, and more. Specifically:

<table>
  <thead>
    <tr>
      <th rowspan="3">FPGA</th>
      <th colspan="2">Toolchain</th>
    </tr>
    <tr></tr>
    <tr>
      <th>Proprietary</th>
      <th>FOSS</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Lattice iCE40</td>
      <td>iCECube2</td>
      <td rowspan="4">Yosys+nextpnr</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Lattice ECP5</td>
      <td rowspan="6">Lattice Diamond</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Lattice MachXO3L</td>
      <td rowspan="14"></td>
    </tr>
    <tr></tr>
    <tr>
      <td>Lattice MachXO2</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Xilinx 7-series</td>
      <td rowspan="4">Vivado</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Xilinx UltraScale</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Xilinx Spartan 6</td>
      <td rowspan="4">ISE</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Xilinx Spartan 3A</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Altera/Intel</td>
      <td>Quartus</td>
    </tr>
    <tr></tr>
    <tr>
      <td>Quicklogic EOS S3</td>
      <td></td>
      <td>Yosys+VPR</td>
    </tr>
  </tbody>
</table>

## License

Torii is released under the [BSD-2-Clause], the full text of which can be found in the [`LICENSE`] file in the root of this repository.

[Amaranth HDL]: https://github.com/amaranth-lang
[Shrine Maiden Heavy Industries]: https://shrine-maiden-heavy.industries/
[torii-boards]: https://github.com/shrine-maiden-heavy-industries/torii-boards
[projects using Torii]: https://torii.shmdn.link/projects.html
[Torii Introduction]: https://torii.shmdn.link/intro.html
[online documentation]: https://torii.shmdn.link
[installation instructions]: https://torii.shmdn.link/install.html
[BSD-2-Clause]: https://spdx.org/licenses/BSD-2-Clause.html
[`LICENSE`]: ./LICENSE
