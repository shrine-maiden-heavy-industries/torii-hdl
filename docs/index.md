<!-- markdownlint-disable MD041 MD033 -->
```{toctree}
:hidden:

intro
install
getting_started/index
tutorials/index
projects
```

```{toctree}
:caption: Language, API, and Library
:hidden:

language/index
api/index
library/index
platforms/index
testing/index
migrations/index

supplementary_libraries

Torii Boards <https://torii-boards.shmdn.link/>
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

Torii is a toolkit for developing hardware based on digital logic, it consists of the [Torii {abbr}`HDL (Hardware Definition Language)`], the [standard library], the simulator, and the build system. It covers all steps of the typical {abbr}`FPGA (Field Programmable Gate Array)` development workflow while not restricting the choice of tools, allowing existing [Verilog], [SystemVerilog], and [VHDL] code to be integrated into the design, while also allow for Torii to be seamlessly integrated into the flow for other [Verilog] design flows.

For more information on Torii, see the [Introduction] and check out the [Getting Started] guide for how to get up and running with Torii.

There is also a [collection of board definition files] for popular FPGA development boards from various vendors, to help you get up to speed with your designs faster.

## Community

The two primary community spots for Torii are the `#torii` IRC channel on [libera.chat] (`irc.libera.chat:6697`) which you can join via your favorite IRC client or the [web chat], and the [discussion forum] on GitHub.

Please do join and share your projects using Torii, ask questions, get help with problems, or discuss Torii's development.

We also maintain a list of [projects using Torii], so post it in the [show and tell] section of the [discussion forum] and we'll add it!

[Verilog]: https://ieeexplore.ieee.org/document/1620780
[SystemVerilog]: https://ieeexplore.ieee.org/document/8299595
[VHDL]: https://ieeexplore.ieee.org/document/8938196
[Torii {abbr}`HDL (Hardware Definition Language)`]: ./language/index.md
[standard library]: ./library/index.md
[Introduction]: ./intro.md
[Getting Started]: ./getting_started/index.md
[collection of board definition files]: https://torii-boards.shmdn.link/
[libera.chat]: https://libera.chat/
[web chat]: https://web.libera.chat/#torii
[discussion forum]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/discussions
[projects using Torii]: ./projects.md
[show and tell]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/discussions/categories/show-and-tell
