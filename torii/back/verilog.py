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

def _convert_rtlil_text(
	rtlil_text: str, *, strip_internal_attrs: bool = False, write_verilog_opts: tuple[str, ...] = ()
) -> str:

	yosys = find_yosys()

	script = []
	script.append(f'read_rtlil <<rtlil\n{rtlil_text}\nrtlil')

	script.append('proc -nomux -norom')
	script.append('memory_collect')

	if strip_internal_attrs:
		attr_map = []
		attr_map.append('-remove generator')
		attr_map.append('-remove top')
		attr_map.append('-remove src')
		attr_map.append('-remove torii.hierarchy')
		attr_map.append('-remove torii.decoding')
		script.append(f'attrmap {" ".join(attr_map)}')
		script.append(f'attrmap -modattr {" ".join(attr_map)}')

	script.append(f'write_verilog -norename {" ".join(write_verilog_opts)}')

	return yosys.run(
		['-q', '-'], '\n'.join(script),
		# At the moment, Yosys always shows a warning indicating that not all processes can be
		# translated to Verilog. We carefully emit only the processes that *can* be translated, and
		# squash this warning. Once Yosys' write_verilog pass is fixed, we should remove this.
		ignore_warnings = True
	)

def convert_fragment(
	fragment: Fragment, name: str = 'top', emit_src: bool = True, strip_internal_attrs: bool = False
) -> tuple[str, SignalDict]:
	'''
	Recursively lower the given Torii :py:class:`Fragment <torii.hdl.ir.Fragment>` into Verilog text and
	a signal map.

	Parameters
	----------
	fragment : torii.hdl.ir.Fragment
		The Torii fragment hierarchy to lower.
	name : str
		The name of the root fragment module.

	emit_src : bool
		Emit source line attributes in the resulting Verilog text.

	strip_internal_attrs : bool
		Remove Torii-specific attributes that were emitted into the resulting Verilog text.

	Returns
	-------
	tuple[str, torii.hdl.ast.SignalDict]
		The Verilog text and signal dictionary of the lowered fragment.
	'''

	rtlil_text, name_map = rtlil.convert_fragment(fragment, name, emit_src = emit_src)
	return (_convert_rtlil_text(rtlil_text, strip_internal_attrs = strip_internal_attrs), name_map)

def convert(
	elaboratable: Fragment | Elaboratable, name: str = 'top', platform = None, *, ports,
	emit_src: bool = True, strip_internal_attrs: bool = False, missing_domain = lambda name: ClockDomain(name)
) -> str:
	'''
	Convert the given Torii :py:class:`Elaboratable <torii.hdl.ir.Elaboratable>` into Verilog text.

	Parameters
	----------
	elaboratable : torii.hdl.ir.Elaboratable
		The Elaboratable to lower into Verilog.
	name : str
		The name of the resulting Verilog module.

	platform : torii.build.plat.Platform
		The platform to use for Elaboratable evaluation.
	ports : list[]
		The list of ports on the top-level module.
	emit_src : bool
		Emit source line attributes in the final Verilog text.

	strip_internal_attrs : bool
		Remove Torii-specific attributes that were emitted into the resulting Verilog text.

	Returns
	-------
	str
		The resulting Verilog.
	'''

	fragment = Fragment.get(elaboratable, platform).prepare(ports = ports, missing_domain = missing_domain)
	verilog_text, _ = convert_fragment(fragment, name, emit_src = emit_src, strip_internal_attrs = strip_internal_attrs)
	return verilog_text
