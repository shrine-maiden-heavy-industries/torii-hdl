# SPDX-License-Identifier: BSD-2-Clause

from ..hdl.ast     import SignalDict
from ..hdl.cd      import ClockDomain
from ..hdl.ir      import Elaboratable, Fragment
from ..tools.yosys import find_yosys
from .             import rtlil

__all__ = (
	'convert_fragment',
	'convert',
)

def _convert_rtlil_text(rtlil_text: str, *, write_json_opts: tuple[str, ...] = ()) -> str:

	yosys = find_yosys()

	script = []
	script.append(f'read_rtlil <<rtlil\n{rtlil_text}\nrtlil')

	script.append('proc -noopt -norom')
	script.append('memory_collect')

	script.append(f'write_json {" ".join(write_json_opts)}')

	return yosys.run(['-q', '-'], '\n'.join(script))

def convert_fragment(fragment: Fragment, name: str = 'top', emit_src: bool = True) -> tuple[str, SignalDict]:
	'''
	Recursively lower the given Torii :py:class:`Fragment <torii.hdl.ir.Fragment>` into a JSON netlist and
	a signal map.

	Parameters
	----------
	fragment : torii.hdl.ir.Fragment
		The Torii fragment hierarchy to lower.

	name : str
		The name of the root fragment module.

	emit_src : bool
		Emit source line attributes in the resulting JSON.

	Returns
	-------
	tuple[str, torii.hdl.ast.SignalDict]
		The JSON netlist and signal dictionary of the lowered fragment.
	'''

	rtlil_text, name_map = rtlil.convert_fragment(fragment, name, emit_src = emit_src)
	return (_convert_rtlil_text(rtlil_text), name_map)

def convert(
	elaboratable: Fragment | Elaboratable, name: str = 'top', platform = None, *, ports,
	emit_src: bool = True, strip_internal_attrs: bool = False, missing_domain = lambda name: ClockDomain(name)
) -> str:
	'''
	Convert the given Torii :py:class:`Elaboratable <torii.hdl.ir.Elaboratable>` into a JSON netlist.

	Parameters
	----------
	elaboratable : torii.hdl.ir.Elaboratable
		The Elaboratable to write the JSON netlist for.

	name : str
		The name of the resulting JSON netlist.

	platform : torii.build.plat.Platform
		The platform to use for Elaboratable evaluation.

	ports : list[]
		The list of ports on the top-level module.

	emit_src : bool
		Emit source line attributes in the final JSON netlist.

	Returns
	-------
	str
		The resulting JSON netlist.
	'''

	fragment = Fragment.get(elaboratable, platform).prepare(ports = ports, missing_domain = missing_domain)
	json_netlist, _ = convert_fragment(fragment, name, emit_src = emit_src)
	return json_netlist
