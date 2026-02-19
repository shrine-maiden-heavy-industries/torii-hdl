<!-- markdownlint-disable MD014 -->
# Installation

:::{warning}
The following instructions are a work-in-progress and may not be entirely up to date, or work for the target system, if you run into anything, please [report an issue]!
:::

## System requirements

Torii requires Python 3.10 or newer, and has been tested with [CPython] and [PyPy], but only CPython is officially supported.

In addition, Torii also requires a copy of [Yosys] version 0.30 or newer, excluding version 0.37 due to a bug in the Verilog backend.

These are the only two "hard" requirements for Torii, you can do things like simulation without any additional software, however to view simulation results, a waveform viewer such as [surfer] or [GTKWave] is invaluable for debugging. Formal verification support, additionally needs [sby] and an SMT solver such as [Yices] or [Bitwuzla].

To synthesize, place-and-route, and pack a Torii design for an FPGA, you need the toolchain specific to the family of FPGA you are targeting, see the [platform] specific documentation for more information regarding vendor toolchains.

## Installing Prerequisites

Prior to installing Torii, install the required system prerequisites, and optionally the prerequisites for [simulation] and [formal] support.

### Python and `pip`

First off, install `python` and `pip` as appropriate on your system if it's not done so already.

::::{tab} Linux
:::{tab} Arch-like

```console
$ sudo pacman -S python python-pip
```

:::
:::{tab} Fedora-like

```console
$ sudo dnf install python3 python3-pip
```

:::
:::{tab} Debian-like

```console
$ sudo apt install python3 python3-pip
```

:::
:::{tab} SUSE-like

```console
$ sudo zypper install python3 python3-pip
```

:::
::::
::::{tab} macOS
Install [Homebrew](https://brew.sh/) if not done already, then install the requirements.

```console
$ brew install python
```

::::
::::{tab} Windows
Download the latest Python installer from the [Python downloads](https://www.python.org/downloads/) page.

Follow the instructions and ensure that the installer installs `pip` and puts the python executable in your `%PATH%`
::::

### Yosys

::::::{tab} Linux
There are two primary ways to get a copy of Yosys for your system, the first is with the systems package manager, a.k.a "Native", or via pre-build binary distributions provided by [YosysHQ] known as the [OSS CAD Suite].

The OSS CAD Suite is very large and has lots of extra things, such as it's own version of python, and a suite of other tools, it's very convenient, but can cause some problems if you're using it for your primary environment for Torii.

There is also a distribution of the Yosys toolchain built to target WASM and installable from [PyPI] called [YoWASP], currently Torii is not able to find a Yosys install from these so it is not a viable way to install Yosys for Torii to use at the moment.

:::::{tab} Native
::::{tab} Arch-like

```console
$ sudo pacman -S yosys
```

On Arch Linux and Arch-likes, you can install nightly Yosys packages which are located in the [AUR] with an AUR helper or using manually using `makepkg` directly.

:::{tab} AUR

```console
$ yay -S yosys-nightly
```

:::
:::{tab} Manual

```console
$ git clone https://aur.archlinux.org/yosys-nightly.git
$ (cd yosys-nightly && makepkg -sic)
```

:::
::::
::::{tab} Fedora-like

```console
$ sudo dnf install yosys
```

::::
::::{tab} Debian-like
:::{todo}
Find a source for deb packages
:::
::::
::::{tab} SUSE-like
:::{todo}
Find a source for suse packages
:::
::::
:::::
:::::{tab} OSS-CAD-Suite
Simply download the latest [OSS-CAD-Suite release] for your architecture, extract it to a good home, and then add it to your `$PATH`

```console
$ curl -LOJ https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-09-10/oss-cad-suite-linux-x64-20250910.tgz
$ tar xf oss-cad-suite-linux-x64-20250910.tgz
$ export PATH="$PATH:`pwd`/oss-cad-suite/bin"
```

:::::
:::::{tab} YoWASP
:::{todo}
YoWASP Support
:::
:::::
::::::
:::::{tab} macOS
For macOS systems it is recommended to use the [OSS CAD Suite] provided by [YosysHQ].

There is also a distribution of the Yosys toolchain built to target WASM and installable from [PyPI] called [YoWASP], currently Torii is not able to find a Yosys install from these so it is not a viable way to install Yosys for Torii to use at the moment.

::::{tab} OSS-CAD-Suite
Simply download the latest [OSS-CAD-Suite release] for your architecture, extract it to a good home, and then add it to your `$PATH`.

```console
$ curl -LOJ https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-09-10/oss-cad-suite-darwin-arm64-20250910.tgz
$ tar xf oss-cad-suite-darwin-arm64-20250910.tgz
$ export PATH="$PATH:`pwd`/oss-cad-suite/bin"
```

::::
::::{tab} YoWASP
:::{todo}
YoWASP Support
:::
::::
:::::
:::::{tab} Windows
For Windows systems it is recommended to use the [OSS CAD Suite] provided by [YosysHQ].

There is also a distribution of the Yosys toolchain built to target WASM and installable from [PyPI] called [YoWASP], currently Torii is not able to find a Yosys install from these so it is not a viable way to install Yosys for Torii to use at the moment.

::::{tab} OSS-CAD-Suite
Simply download the latest [OSS-CAD-Suite release] for your architecture, extract it to a good home, and then add it to your `%PATH%`.

```console
$ call %cd%\oss-cad-suite\environment.bat
```

::::
::::{tab} YoWASP
:::{todo}
YoWASP Support
:::
::::
:::::

### Waveform Viewer (Optional)

An EDA Waveform Viewer is optional, but highly recommended. [GTKWave] is the standard of the Open Source EDA world, and has been around for a long time, and is what you will find most tutorials using. On the other hand, [surfer] is an up-and-coming waveform viewer that's written in Rust and is able to run in your web browser via WASM.

::::::{tab} Linux
There are two primary ways to get a waveform viewer for your system, the first is with the systems package manager, a.k.a "Native", or via pre-build binary distributions provided by [YosysHQ] known as the [OSS CAD Suite].

The OSS CAD Suite only provides GTKWave, so if you wish to use surfer instead see the Native install options.

:::::{tab} Native
::::{tab} GTKWave
:::{tab} Arch-like

```console
$ sudo pacman -S gtkwave
```

:::
:::{tab} Fedora-like

```console
$ sudo dnf install gtkwave
```

:::
:::{tab} Debian-like

```console
$ sudo apt install gtkwave
```

:::
:::{tab} SUSE-like

```console
$ sudo zypper install gtkwave
```

:::
::::
::::{tab} Surfer
There are two ways to install Surfer, the first is from source, and the other is using a pre-built binary.

Please see the [surfer installation instructions] for up-to-date installation instructions for your platform.
::::
:::::
:::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds come bundled with a copy of GTKWave. If you wish to use surfer, see the Native install instructions.
:::::
::::::
::::::{tab} macOS
:::::{tab} GTKWave
::::{tab} Native
:::{todo}
Instructions
:::
::::
::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds come bundled with a copy of GTKWave. If you wish to use surfer, see the Native install instructions.
::::
:::::
:::::{tab} Surfer
There are two ways to install Surfer, the first is from source, and the other is using a pre-built binary.

Please see the [surfer installation instructions] for up-to-date installation instructions for your platform.
:::::
::::::
::::::{tab} Windows
:::::{tab} GTKWave
::::{tab} Native
:::{todo}
Instructions
:::
::::
::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds come bundled with a copy of GTKWave. If you wish to use surfer, see the Native install instructions.
::::
:::::
:::::{tab} Surfer
There are two ways to install Surfer, the first is from source, and the other is using a pre-built binary.

Please see the [surfer installation instructions] for up-to-date installation instructions for your platform.
:::::
::::::

### Formal Tools (Optional)

:::::::{tab} Linux
::::::{tab} Native
:::::{tab} Arch-like
On Arch Linux and Arch-likes, you can install nightly sby packages which are located in the [AUR] with an AUR helper or manually using `makepkg` directly.

::::{tab} AUR

```console
$ yay -S sby-nightly
```

::::
::::{tab} Manual

```console
$ git clone https://aur.archlinux.org/sby-nightly.git
$ (cd yosys-nightly && makepkg -sic)
```

::::
:::::
:::::{tab} Fedora-like
::::{todo}
Instructions
::::
:::::
:::::{tab} Debian-like
::::{todo}
Instructions
::::
:::::
:::::{tab} SUSE-like
::::{todo}
Instructions
::::
:::::
::::::
::::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds already include `sby` as well as a suite of SMT solvers.
::::::
:::::::
:::::{tab} macOS
::::{tab} Native
:::{todo}
Instructions
:::
::::
::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds already include `sby` as well as a suite of SMT solvers.
::::
:::::
:::::{tab} Windows
::::{tab} Native
:::{todo}
Instructions
:::
::::
::::{tab} OSS-CAD-Suite
The OSS-CAD-Suite builds already include `sby` as well as a suite of SMT solvers.
::::
:::::

## Installing Torii

The latest stable release of Torii is recommended for any new projects planning to use Torii. It provides the most up-to-date stable version of the API. However, if needed, you can also install a development snapshot to get access to the bleeding-edge, however things might break.

:::{tab} Stable Release
The stable release of Torii can be installed directly from [PyPI](https://pypi.org/project/torii/).

```console
$ pip3 install --user --upgrade torii
```

:::
:::::{tab} Development Snapshot
There are two possible ways to install a development snapshot for Torii, the first is using `pip` and to get it directly from GitHub.

The other way is to have a local git clone of the repository and install it in an editable manner, this is recommended if you plan to do any development work on Torii itself.

::::{tab} Standard

```console
$ pip3 install --user 'torii @ git+https://github.com/shrine-maiden-heavy-industries/torii-hdl.git'
```

::::
::::{tab} Editable

```console
$ git clone https://github.com/shrine-maiden-heavy-industries/torii-hdl
$ cd torii-hdl
$ pip3 install --user --editable '.'
```

Any changes made to the `torii-hdl` directory will immediately affect any code that uses Torii. To update the snapshot, run:

```console
$ cd torii-hdl
$ git pull --ff-only origin main
$ pip3 install --user --editable '.'
```

Run the `pip3 install --editable .` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an `ImportError`.
::::
:::::

## Installing Board Definitions

The [Torii Boards] package includes a collection of pre-made board files for various FPGA development boards, it is generally useful to have.

Just like with Torii proper, there are two versions you can install, the latest stable, or the development version.

:::{tab} Stable Release
The stable release of Torii Boards can be installed directly from [PyPI](https://pypi.org/project/torii-boards/).

```console
$ pip3 install --user --upgrade torii-boards
```

:::
:::::{tab} Development Snapshot
There are two possible ways to install a development snapshot for the board support package, the first is using `pip` and to get it directly from GitHub.

The other way is to have a local git clone of the repository and install it in an editable manner, this is recommended if you plan to do any development work on the board files themselves.

::::{tab} Standard

```console
$ pip3 install --user 'torii-boards @ git+https://github.com/shrine-maiden-heavy-industries/torii-boards.git'
```

::::
::::{tab} Editable

```console
$ git clone https://github.com/shrine-maiden-heavy-industries/torii-boards
$ cd torii-boards
$ pip3 install --user --editable '.'
```

Any changes made to the `torii-boards` directory will immediately affect any code that uses the board definitions.

To update the snapshot, run:

```console
$ cd torii-boards
$ git pull --ff-only origin main
$ pip3 install --user --editable '.'
```

Run the `pip3 install --editable .` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an `ImportError`.

::::
:::::

## Next Steps

Now that you've installed Torii, see the [getting started] guide for a quick introduction, and the [language guide] for more in-depth documentation on the language.

[report an issue]: https://github.com/shrine-maiden-heavy-industries/torii-hdl/issues
[CPython]: https://www.python.org/
[PyPy]: https://pypy.org/
[Yosys]: https://github.com/YosysHQ/yosys
[YosysHQ]: https://github.com/YosysHQ
[OSS CAD Suite]: https://github.com/YosysHQ/oss-cad-suite-build/tree/main
[OSS-CAD-Suite release]: https://github.com/YosysHQ/oss-cad-suite-build/releases
[PyPI]: https://pypi.org/
[YoWASP]: https://yowasp.org/
[AUR]: https://aur.archlinux.org/
[GTKWave]: https://github.com/gtkwave/gtkwave
[surfer]: https://surfer-project.org/
[surfer installation instructions]: https://gitlab.com/surfer-project/surfer#installation
[platform]: ./platforms/index.md
[sby]: https://github.com/YosysHQ/sby
[yices]: https://github.com/SRI-CSL/yices2
[bitwuzla]: https://bitwuzla.github.io/
[simulation]: #waveform-viewer-optional
[formal]: #formal-tools-optional
[Torii Boards]: https://github.com/shrine-maiden-heavy-industries/torii-boards
[getting started]: ./getting_started/index.md
[language guide]: ./language/index.md
