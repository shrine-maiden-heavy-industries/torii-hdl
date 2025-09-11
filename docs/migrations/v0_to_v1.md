# Torii v0.X to v1.0 Migration Guide

:::{todo}
This document is a work in progress and should be updated as the progression v1.0 progresses
:::

## General

### HDL Constructs Imported From Root `torii` Namespace

The Previous versions of Torii let you do a general glob import of all of the core HDL constructs ({py:class}`Signal <torii.hdl.ast.Signal>` et. al.) from the root {py:mod}`torii` module namespace.

These must now be imported from the {py:mod}`torii.hdl` module namespace, and while glob imports are discouraged, they will still work as intended previously.

```python
# OLD (<1.0.0)
from torii import *

# NEW (>=1.0.0)
from torii.hdl import *
```

### Importing `YosysError` from `torii.back.cxxrtl` and `torii.back.verilog`

The ability to directly import {py:class}`YosysError <torii.tools.yosys.YosysError>` from the {py:mod}`torii.back.cxxrtl` and {py:mod}`torii.back.verilog` modules has been removed, as it made little sense logically.

It must now be directly imported from {py:mod}`torii.tools.yosys` itself.

```python
# OLD (<1.0.0)
from torii.back.cxxrtl import YosysError
# -- OR --
from torii.back.verilog import YosysError

# NEW (>=1.0.0)
from torii.tools.yosys import YosysError
```

### `DIR_FANIN`/`DIR_FANOUT`/`DIR_NONE` from `torii.hdl.rec`

The `DIR_FANIN`, `DIR_FANOUT`, and `DIR_NONE` constant aliases have been removed in favor of using the {py:class}`Direction <torii.hdl.rec.Direction>` enumeration directly.

```python
# OLD (<1.0.0)
from torii.hdl.rec import DIR_FANIN, DIR_FANOUT, DIR_NONE

rec = Record([
	('a', 1, DIR_FANIN),
	('b', 1, DIR_FANOUT),
	('c', 1, DIR_NONE),
])

# NEW (>=1.0.0)
from torii.hdl.rec import Direction

rec = Record([
	('a', 1, Direction.FANIN),
	('b', 1, Direction.FANOUT),
	('c', 1, Direction.NONE),
])
```

While it is a touch more wordy, we feel it give more context and is generally more descriptive.

### `build_cxx` from `torii.tools.cxx`

The `build_cxx` function from {py:mod}`torii.tools.cxx` has been removed in favor of the {py:func}`compile_cxx <torii.tools.cxx.compile_cxx>`, which offers more control and capabilities.

```python
# OLD (<1.0.0)
from torii.tools.cxx import build_cxx

build_dir, output_file = build_cxx(
	cxx_sources = {
		'foo.cc': '/* Source Code for foo */'
	},
	output_name  = 'foo',
	include_dirs = [],
	macros       = []
)

# NEW (>=1.0.0)
from torii.tools.cxx import compile_cxx

output_file = compile_cxx(
	'foo',
	build_dir,
	None,
	source_listings = {
		'foo.cc': '/* Source for foo */'
	}
)

```

For more information see the full documentation on {py:func}`compile_cxx <torii.tools.cxx.compile_cxx>` for all of it's capabilities and examples of more advanced usage.

The equivalent functionality can be maintained with a little bit of scaffolding:

```python
def build_cxx(
	cxx_sources: dict[str, str], output_name: str, include_dirs: list[str], macros: list[str]
)  -> tuple[TemporaryDirectory[str], str]:

	build_dir  = TemporaryDirectory(prefix = 'torii_cxx_')
	output_dir = Path(build_dir.name)

	output_file = compile_cxx(
		output_name, output_dir, None, include_paths = include_dirs, defines = {
			k: v for (k, v) in (macro.strip().split('=', 2) for macro in macros)
		},
		source_listings = cxx_sources
	)

	return (build_dir, output_file.name)
```

### `@extend` from `torii.util.decorators`

The `@extend` decorator from the {py:mod}`torii.util.decorators` module has been removed outright. There is no replacement for this as it involved injecting things into other classes which breaks the type system and in general was a bad idea.

### `@memoize` from `torii.util.decorators`

The `@memoize` decorator from {py:mod}`torii.util.decorators` has been removed and should be replaced with {py:class}`functools.cache`.

```python
# OLD (<1.0.0)
from torii.util.decorators import memoize

@memoize
def foo(bar: int, baz: int) -> int:
	...

# NEW (>=1.0.0)
from functools import cache

@cache
def foo(bar: int, baz: int) -> int:
	...
```

## Library Changes

### `torii.lib.soc.memory`

The contents of the `torii.lib.soc.memory` module have been moved to {py:mod}`torii.lib.mem`, as they are generally useful for non-SoC designs as well as SoC designs.

More specifically the {py:class}`MemoryMap <torii.lib.mem.map.MemoryMap>`, {py:class}`ResourceInfo <torii.lib.mem.map.ResourceInfo>`, and {py:class}`_RangeMap <torii.lib.mem.map._RangeMap>` have been moved to {py:mod}`torii.lib.mem.map`.

```python
# OLD (<1.0.0)
from torii.lib.soc.memory import MemoryMap, ResourceInfo

# NEW (>=1.0.0)
from torii.lib.mem.map import MemoryMap, ResourceInfo
```

### `torii.lib.soc.wishbone`

The `wishbone` module has been removed from {py:mod}`torii.lib.soc` and moved to {py:mod}`torii.lib.bus.wishbone`, as it is generally useful for non-SoC designs as well as SoC designs, and is not the only bus type supported.

```python
# OLD (<1.0.0)
from torii.lib.soc.wishbone import Arbiter, Interface

# -- OR --
from torii.lib.soc.wishbone.bus import Arbiter, Interface

# NEW (>=1.0.0)
from torii.lib.bus.wishbone import Arbiter, Interface
```

## Module Changes

### `DomainRenamer` from `torii.hdl.xfrm`

In past versions of Torii, you could use the {py:class}`DomainRenamer <torii.hdl.xfrm.DomainRenamer>` in two ways, the first was to pass a single string into it, which would be used to re-map the `sync` domain in the wrapped elaboratables to that domain, or pass a dictionary literally to map one or more domains.

These have been replaced with using `kwargs` to more directly display the intent of the renamer over passing a single string, and also to clean up visual noise when passing a dictionary.

```python
from torii.hdl import DomainRenamer

# OLD (<1.0.0)

a = DomainRenamer('meow')(elab)
# -- OR --
a = DomainRenamer({'sync': 'meow'})(elab)

# NEW (>=1.0.0)
a = DomainRenamer(sync = 'meow')(elab)
```

If you need to pass a dictionary that is built at runtime to the domain renamer, then you can simply un-pack the dictionary into the constructor like so:

```python
from torii.hdl import DomainRenamer

domain_map = {
	'sync': 'meow',
	# ...
}

# OLD (<1.0.0)
a = DomainRenamer(domain_map)(elab)

# NEW (>=1.0.0)
a = DomainRenamer(**domain_map)(elab)
```

### `StreamInterface` from `torii.lib.stream.simple`

The {py:class}`StreamInterface <torii.lib.stream.simple.StreamInterface>` from {py:mod}`torii.lib.stream.simple` has had the `connect` method removed in favor of the `attach` method. In addition the `payload` signal has been removed in favor of the `data` signal.

```python
from torii.lib.stream.simple import StreamInterface

foo      = Signal(8)

stream_a = StreamInterface()
stream_b = StreamInterface()

# OLD (<1.0.0)
stream_a.connect(stream_b)

# ...

m.d.comb += [
	foo.eq(stream_a.payload),
]

# NEW (>=1.0.0)
stream_a.attach(stream_a)

# ...

m.d.comb += [
	foo.eq(stream_a.data),
]
```

### `AsyncSerialRX` from `torii.lib.stdio.serial`

The {py:class}`AsyncSerialRX <torii.lib.stdio.serial.AsyncSerialRX>` from {py:mod}`torii.lib.stdio.serial` has had the `rdy` and `ack` signals removed in favor of the `done` and `start` signals respectively.

This was done to match them more logically to what they actually do in order to avoid common pitfalls and confusion when using the module.

```python
from torii.lib.stdio.serial import AsyncSerialRX

uart_rx = AsyncSerialRX(...)

# OLD (<1.0.0)

with m.FSM(name = 'rx') as fsm:
	m.d.comb += [ uart_rx.ack.eq(fsm.ongoing('IDLE')), ]

	with m.State('IDLE'):
		with m.If(uart_rx.rdy):
			m.d.sync += [ data_rx.eq(uart_rx.data), ]
			m.next = 'CMD'

# NEW (>=1.0.0)

with m.FSM(name = 'rx') as fsm:
	m.d.comb += [ uart_rx.start.eq(fsm.ongoing('IDLE')), ]

	with m.State('IDLE'):
		with m.If(uart_rx.done):
			m.d.sync += [ data_rx.eq(uart_rx.data), ]
			m.next = 'CMD'
```
