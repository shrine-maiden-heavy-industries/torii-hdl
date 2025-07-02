# Torii

Torii is a fork of [Amaranth HDL] that has been modified for use at [Shrine Maiden Heavy Industries]. It has merged several of the components that were separate into a single package, and also adds new functionality, as well as some internal changes for better integration into tooling.

The evaluation board definitions have also been migrated and are located in the [torii-boards] repository.

There is also a list of [projects using Torii] that are using Torii, and we'd love to add yours too!

## Introduction, Installation, and Usage

For an [introduction to Torii], [installation instructions], and Usage information, please see the [online documentation].

## Community

The two primary spots for community activity around Torii are the [IRC channel] and the [discussion forum].

Please do join and share your projects using Torii, ask questions, get help with problems, or discuss Torii's development.

## Reporting Issues and Requesting Features

The reporting of bugs and suggestion of features are done GitHub via the [issue tracker], there are pre-defined templates for both of them that will walk you though all the information you need to provide.

Be sure to read the [reporting issues] or the [suggesting features] sections of the [Contribution Guidelines] as appropriate as they go into more important details on the finer points.

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

Torii is released under the [BSD-2-Clause], the full text of which can be found in the [`LICENSE`] file in the root of the [git repository].

The Torii documentation is dual licensed under the [BSD-2-Clause] for all past contributions and the [CC-BY-SA 4.0] for all new and future contributions. The full text of the [CC-BY-SA 4.0] can be found in the [`LICENSE.docs`] file in the root of the [git repository].

[Amaranth HDL]: https://github.com/amaranth-lang
[Shrine Maiden Heavy Industries]: https://shrine-maiden-heavy.industries/
[torii-boards]: https://github.com/shrine-maiden-heavy-industries/torii-boards
[projects using Torii]: https://torii.shmdn.link/latest/projects.html
[issue tracker]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/issues
[reporting issues]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CONTRIBUTING.md#reporting-issues
[suggesting features]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CONTRIBUTING.md#suggesting-features
[Contribution Guidelines]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CONTRIBUTING.md
[introduction to Torii]: https://torii.shmdn.link/latest/intro.html
[online documentation]: https://torii.shmdn.link
[installation instructions]: https://torii.shmdn.link/latest/install.html
[discussion forum]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/discussions
[IRC channel]: https://web.libera.chat/#torii
[BSD-2-Clause]: https://spdx.org/licenses/BSD-2-Clause.html
[`LICENSE`]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/LICENSE
[CC-BY-SA 4.0]: https://creativecommons.org/licenses/by-sa/4.0/
[`LICENSE.docs`]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/LICENSE.docs
[git repository]: https://shrine-maiden-heavy.industries/torii-hdl
