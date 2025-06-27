# Torii v0.X to v1.0 Migration Guide

```{todo}
This document is a work in progress and should be updated as the progression v1.0 progresses
```

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

## Module Changes

### `DomainRenamer`

In past versions of Torii, you could use the {py:class}`DomainRenamer <torii.hdl.xfrm.DomainRenamer>` in two ways, the first was to pass a single string into it, which would be used to re-map the `sync` domain in the wrapped elaboratables to that domain, or pass a dictionary literally to map one or more domains.

These have been replaced with using `kwargs` to more directly display the intent of the renamer over passing a single string, and also to clean up visual noise when passing a dictionary.

```python
DomainRenamer('meow')(elab)

DomainRenamer({'sync': 'meow'})(elab)
```

This should now be written as follows:

```python
DomainRenamer(sync = 'meow')(elab)
```

If you need to pass a dictionary that is built at runtime to the domain renamer, then you can simply un-pack the dictionary into the constructor like so:

```python
DomainRenamer(**domain_map)(elab)
```
