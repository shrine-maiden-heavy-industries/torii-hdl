# Installation

```{warning}
The following instructions are a work-in-progress and may not be entirely up to date.
```


## System requirements

Torii requires Python >= 3.10, and [Yosys](https://github.com/YosysHQ/yosys) >= 0.30 except Yosys version 0.37 due to a Verilog backend bug. Torii has been tested with [CPython](https://www.python.org/), but might possibly run under [PyPy](https://www.pypy.org/).


Simulating Torii code requires no additional software. However, a waveform viewer like [GTKWave](http://gtkwave.sourceforge.net/) is invaluable for debugging.

Synthesizing, placing and routing an Torii design for an FPGA requires the FPGA family specific toolchain. See the [platform](./platforms/index.md) specific documentation for more information regarding vendor toolchains.


## Installing Prerequisites

Prior to installing Torii, you must install all of its prerequisites and requirements.

### Installing Python

First off, install `python` and `pip` onto your system if the're not there already.

```{eval-rst}
.. platform-picker::
	.. platform-choice:: arch
		:title: Arch Linux

		.. code-block:: console

		  $ sudo pacman -S python python-pip

	.. platform-choice:: linux
		:title: Other Linux

		.. warning:: These instructions may be incorrect or incomplete!

		For `Debian <https://www.debian.org/>`_ based systems, use ``apt`` to install ``python3`` and ``python3-pip``

		.. code-block:: console

			$ sudo apt install python3 python3-pip

		For `Fedora <https://getfedora.org/>`_ and other ``dnf`` based systems,

		.. code-block:: console

			$ sudo dnf install python3 python3-pip

	.. platform-choice:: macos
		:title: macOS

		Install `Homebrew <https://brew.sh/>`_ if not done already, then install the requirements.

		.. code-block:: console

		  $ brew install python

	.. platform-choice:: windows
		:title: Windows

		.. warning:: These instructions may be incorrect or incomplete!

		Download the latest Python installer from the `python downloads <https://www.python.org/downloads/>`_ page.

		Follow the instructions and ensure that the installer installs ``pip`` and puts the python executable in your ``%PATH%``

```
### Installing Yosys and GTKWave

```{eval-rst}
.. platform-picker::

	.. platform-choice:: arch
		:title: Arch Linux

		On Arch Linux and Arch-likes, you can install nightly Yosys packages which are located in the `AUR <https://aur.archlinux.org/>`_ with an AUR helper or using ``makepkg`` directly.

		Via an AUR helper like ``yay``

		.. code-block:: console

		  $ yay -S yosys-nightly

		Via ``makepkg`` directly

		.. code-block:: console

		  $ git clone https://aur.archlinux.org/yosys-nightly.git
		  $ (cd yosys-nightly && makepkg -sic)

		And to install GTKWave you can just install it like any normal package

		.. code-block:: console

			$ pacman -S gtkwave

	.. platform-choice:: linux
		:title: Other Linux

		.. warning:: These instructions may be incorrect or incomplete!

		With other Linux distributions, it is recommended to use the `OSS Cad Suite <https://github.com/YosysHQ/oss-cad-suite-build>`_ nightly build. It provides a full environment of all the tools needed built on a nightly basis. This includes Yosys and GTKWave

		Simply download the latest `release <https://github.com/YosysHQ/oss-cad-suite-build/releases>`_ for your architecture, extract it to a good home, and then add it to your ``$PATH``

		.. code-block:: console

		  $ curl -LOJ https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2024-05-04/oss-cad-suite-linux-x64-20240504.tgz
		  $ tar xfv oss-cad-suite-linux-x64-20240504.tgz
		  $ export PATH="`pwd`/oss-cad-suite/bin:$PATH"


	.. platform-choice:: macos
		:title: macOS

		For macOS systems, it is recommended to use the YoWASP distribution of the toolchain. However if you want to use the native tools, and you are using an Intel based Mac, then the `OSS Cad Suite <https://github.com/YosysHQ/oss-cad-suite-build>`_ has nightly builds for x86_64 versions of Darwin. This includes Yosys and GTKWave

		Simply download the latest `release <https://github.com/YosysHQ/oss-cad-suite-build/releases>`_ for your architecture, extract it to a good home, and then add it to your ``$PATH``

		.. code-block:: console

		  $ curl -LOJ https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2024-05-04/oss-cad-suite-darwin-x64-20240504.tgz
		  $ tar xfv oss-cad-suite-darwin-x64-20240504.tgz
		  $ export PATH="`pwd`/oss-cad-suite/bin:$PATH"

	.. platform-choice:: windows
		:title: Windows

		.. warning:: These instructions may be incorrect or incomplete!

		The `OSS Cad Suite <https://github.com/YosysHQ/oss-cad-suite-build>`_ has nightly builds for x86_64 versions of Windows. This includes Yosys and GTKWave

		Simply download the latest `release <https://github.com/YosysHQ/oss-cad-suite-build/releases>`_ for your architecture, extract it to a good home, and then add it to your ``%PATH%``

		.. code-block:: console

			$ call %cd%\oss-cad-suite\environment.bat

```


## Installing Torii


The [latest release](install.md#latest-release) of Torii is recommended for any new projects planning to use Torii. It provides the most up-to-date stable version of the API. However, if needed, you can also install a [development snapshot](install.md#development-snapshot) to get access to the bleeding-edge, however the API may be unstable.


### Latest release

```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		.. code-block:: console

			$ pip3 install --user --upgrade torii

	.. platform-choice:: macos
		:title: macOS

		.. code-block:: console

			$ pip install --user --upgrade torii

	.. platform-choice:: windows
		:title: Windows

		.. code-block:: doscon

			> pip install --upgrade torii

```


### Development snapshot


```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		.. code-block:: console

			$ pip3 install --user 'torii @ git+https://github.com/shrine-maiden-heavy-industries/torii-hdl.git'

	.. platform-choice:: macos
		:title: macOS

		.. code-block:: console

			$ pip install --user 'torii @ git+https://github.com/shrine-maiden-heavy-industries/torii-hdl.git'

	.. platform-choice:: windows
		:title: Windows

		.. code-block:: doscon

			> pip install "torii @ git+https://github.com/shrine-maiden-heavy-industries/torii-hdl.git"

```

### Editable development snapshot


```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		To install an editable development snapshot of Torii for the first time, run:

		.. code-block:: console

			$ git clone https://github.com/shrine-maiden-heavy-industries/torii-hdl
			$ cd torii-hdl
			$ pip3 install --user --editable '.'

		Any changes made to the ``torii-hdl`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: console

			$ cd torii-hdl
			$ git pull --ff-only origin main
			$ pip3 install --user --editable '.'

		Run the ``pip3 install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.

	.. platform-choice:: macos
		:title: macOS

		To install an editable development snapshot of Torii for the first time, run:

		.. code-block:: console

			$ git clone https://github.com/shrine-maiden-heavy-industries/torii-hdl
			$ cd torii-hdl
			$ pip install --user --editable '.'

		Any changes made to the ``torii-hdl`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: console

			$ cd torii-hdl
			$ git pull --ff-only origin main
			$ pip install --user --editable '.'

		Run the ``pip install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.

	.. platform-choice:: windows
		:title: Windows

		To install an editable development snapshot of Torii for the first time, run:

		.. code-block:: doscon

			> git clone https://github.com/shrine-maiden-heavy-industries/torii-hdl
			> cd torii-hdl
			> pip install --editable .

		Any changes made to the ``torii-hdl`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: doscon

			> cd torii-hdl
			> git pull --ff-only origin main
			> pip install --editable .

		Run the ``pip install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.


```

## Installing board definitions

This section assumes you have already [installed Torii](#installation) to your system.

Installing the [Torii Development Board](https://github.com/shrine-maiden-heavy-industries/torii-boards) definitions is much the same as installing Torii.

### Latest release

```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		.. code-block:: console

			$ pip3 install --user --upgrade torii-boards

	.. platform-choice:: macos
		:title: macOS

		.. code-block:: console

			$ pip install --user --upgrade torii-boards

	.. platform-choice:: windows
		:title: Windows

		.. code-block:: doscon

			> pip install --upgrade torii-boards

```


### Development snapshot


```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		.. code-block:: console

			$ pip3 install --user 'git+https://github.com/shrine-maiden-heavy-industries/torii-boards.git#egg=torii-boards'

	.. platform-choice:: macos
		:title: macOS

		.. code-block:: console

			$ pip install --user 'git+https://github.com/shrine-maiden-heavy-industries/torii-boards.git#egg=torii-boards'

	.. platform-choice:: windows
		:title: Windows

		.. code-block:: doscon

			> pip install git+https://github.com/shrine-maiden-heavy-industries/torii-boards.git#egg=torii-boards

```

### Editable development snapshot


```{eval-rst}
.. platform-picker::

	.. platform-choice:: linux
		:title: Linux

		To install an editable development snapshot of　``torii-boards`` for the first time, run:

		.. code-block:: console

			$ git clone https://github.com/shrine-maiden-heavy-industries/torii-boards
			$ cd torii-boards
			$ pip3 install --user --editable '.'

		Any changes made to the ``torii-boards`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: console

			$ cd torii-boards
			$ git pull --ff-only origin main
			$ pip3 install --user --editable '.'

		Run the ``pip3 install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.

	.. platform-choice:: macos
		:title: macOS

		To install an editable development snapshot of ``torii-boards`` for the first time, run:

		.. code-block:: console

			$ git clone https://github.com/shrine-maiden-heavy-industries/torii-boards
			$ cd torii-boards
			$ pip install --user --editable '.'

		Any changes made to the ``torii-boards`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: console

			$ cd torii-boards
			$ git pull --ff-only origin main
			$ pip install --user --editable '.'

		Run the ``pip install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.

	.. platform-choice:: windows
		:title: Windows

		To install an editable development snapshot of ``torii-boards`` for the first time, run:

		.. code-block:: doscon

			> git clone https://github.com/shrine-maiden-heavy-industries/torii-boards
			> cd torii-boards
			> pip install --editable .

		Any changes made to the ``torii-boards`` directory will immediately affect any code that uses Torii. To update the snapshot, run:

		.. code-block:: doscon

			> cd torii-boards
			> git pull --ff-only origin main
			> pip install --editable .

		Run the ``pip install --editable .`` command each time the editable development snapshot is updated in case package dependencies have been added or changed. Otherwise, code using Torii may misbehave or crash with an ``ImportError``.


```
