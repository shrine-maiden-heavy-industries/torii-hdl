```{toctree}
:hidden:

intro
install
getting_started
tutorials/index
language/index
api/index
library/index
platforms/index
testing/index

external_libraries
migration_guide
projects

Torii Boards <https://shrine-maiden-heavy-industries.github.io/torii-boards/>
```

```{toctree}
:caption: Development
:hidden:

Source Code <https://github.com/shrine-maiden-heavy-industries/torii-hdl/>
Contributing <https://github.com/shrine-maiden-heavy-industries/torii-hdl/blob/main/CONTRIBUTING.md>
changelog
license

```

# Torii-HDL

```{warning}
   This manual is a work in progress and is seriously incomplete!
```

Torii is a toolkit for developing hardware based on digital logic, it consists of the　[Torii <abbr title="Hardware Definition Language">HDL</abbr>], the [standard library], the simulator, and the build system. It covers all steps of the typical <abbr title="Field Programmable Gate Array">FPGA</abbr> development workflow while not restricting the choice of tools, allowing existing [Verilog], [SystemVerilog], and [VHDL] code to be integrated into the design, while also allow for Torii to be seamlessly integrated into the flow for other [Verilog] design flows.

For more information on Torii, see the [Introduction] and check out the [Getting Started] guide for how to get up and running with Torii.

There is also a [collection of board definition files] for popular FPGA development boards from various vendors, to help you get up to speed with your designs faster.

[Verilog]: https://ieeexplore.ieee.org/document/1620780
[SystemVerilog]: https://ieeexplore.ieee.org/document/8299595
[VHDL]: https://ieeexplore.ieee.org/document/8938196
[Torii <abbr title="Hardware Definition Language">HDL</abbr>]: ./language/index.md
[standard library]: ./library/index.md
[Introduction]: ./intro.md
[Getting Started]: ./getting_started.md
[collection of board definition files]: https://torii-boards.shmdn.link/
