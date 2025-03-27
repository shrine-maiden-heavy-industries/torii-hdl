# SPDX-License-Identifier: BSD-2-Clause

from warnings      import warn

from ..hdl.ast     import SignalDict
from ..hdl.cd      import ClockDomain
from ..hdl.ir      import Elaboratable, Fragment
from ..tools.yosys import YosysError, find_yosys
from .             import rtlil

__all__ = (
	'convert_fragment',
	'convert',
)

def __dir__() -> list[str]:
	return list({*globals(), *__all__, 'YosysError'})

def __getattr__(name: str):
	if name == 'YosysError':
		warn(
			'Importing \'YosysError\' from this module has been deprecated, '
			'please import it from \'torii.tools.yosys\' instead.',
			DeprecationWarning,
			stacklevel = 2
		)
		return YosysError
	if name not in __dir__():
		raise AttributeError(f'Module {__name__!r} has not attribute {name!r}')

def _convert_rtlil_text(
	rtlil_text: str, black_boxes: dict[str, str] | None, *, src_loc_at: int = 0
) -> str:
	if black_boxes is not None:
		if not isinstance(black_boxes, dict):
			raise TypeError(f'CXXRTL black boxes must be a dictionary, not {black_boxes!r}')
		for box_name, box_source in black_boxes.items():
			if not isinstance(box_name, str):
				raise TypeError(f'CXXRTL black box name must be a string, not {box_name!r}')
			if not isinstance(box_source, str):
				raise TypeError(f'CXXRTL black box source code must be a string, not {box_source!r}')

	yosys = find_yosys()

	script = []
	if black_boxes is not None:
		for box_name, box_source in black_boxes.items():
			script.append(f'read_rtlil <<rtlil\n{box_source}\nrtlil')
	script.append(f'read_rtlil <<rtlil\n{rtlil_text}\nrtlil')
	script.append('write_cxxrtl')

	return yosys.run(['-q', '-'], '\n'.join(script), src_loc_at = 1 + src_loc_at)

def convert_fragment(
	fragment: Fragment, name: str = 'top', emit_src: bool = True, black_boxes: dict[str, str] | None = None,
) -> tuple[str, SignalDict]:
	'''
	Recursively lower the given Torii :py:class:`Fragment <torii.hdl.ir.Fragment>` into CXXRTL text and
	a signal map.

	Parameters
	----------
	fragment : torii.hdl.ir.Fragment
		The Torii fragment hierarchy to lower.
	name : str
		The name of the root fragment module.
		(default: 'top')
	emit_src : bool
		Emit source line attributes in the resulting CXXRTL text.
		(default: True)
	black_boxes : dict[str, str]
		A map of CXXRTL blackboxes to use in the resulting design.

	Returns
	-------
	tuple[str, torii.hdl.ast.SignalDict]
		The CXXRTL text and signal dictionary of the lowered fragment.
	'''

	rtlil_text, name_map = rtlil.convert_fragment(fragment, name, emit_src = emit_src)
	return (_convert_rtlil_text(rtlil_text, black_boxes, src_loc_at = 1), name_map)

def convert(
	elaboratable: Elaboratable, name: str = 'top', platform = None, black_boxes: dict[str, str] | None = None, *,
	ports, emit_src: bool = True, missing_domain = lambda name: ClockDomain(name)
) -> str:
	'''
	Convert the given Torii :py:class:`Elaboratable <torii.hdl.ir.Elaboratable>` into CXXRTL text.

	Parameters
	----------
	elaboratable : torii.hdl.ir.Elaboratable
		The Elaboratable to lower into Verilog.
	name : str
		The name of the resulting Verilog module.
		(default: 'top')
	platform : torii.build.plat.Platform
		The platform to use for Elaboratable evaluation.
	ports : list[]
		The list of ports on the top-level module.
	emit_src : bool
		Emit source line attributes in the final CXXRTL text.
		(default: True)
	black_boxes : dict[str, str]
		A map of CXXRTL blackboxes to use in the resulting design.

	Returns
	-------
	str
		The resulting CXXRTL.
	'''

	rtlil_text = rtlil.convert(
		elaboratable, name, platform, ports = ports, emit_src = emit_src, missing_domain = missing_domain
	)
	return _convert_rtlil_text(rtlil_text, black_boxes, src_loc_at = 1)
