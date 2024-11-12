# SPDX-License-Identifier: BSD-2-Clause

from ..hdl         import ast, ir
from ..tools.yosys import YosysError, find_yosys
from .             import rtlil

__all__ = (
	'convert_fragment',
	'convert',
	'YosysError',
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

	return yosys.run(['-q', '-'], '\n'.join(script),
		# At the moment, Yosys always shows a warning indicating that not all processes can be
		# translated to Verilog. We carefully emit only the processes that *can* be translated, and
		# squash this warning. Once Yosys' write_verilog pass is fixed, we should remove this.
		ignore_warnings = True
	)


def convert_fragment(*args, strip_internal_attrs: bool = False, **kwargs) -> tuple[str, ast.SignalDict]:
	rtlil_text, name_map = rtlil.convert_fragment(*args, **kwargs)
	return (_convert_rtlil_text(rtlil_text, strip_internal_attrs = strip_internal_attrs), name_map)


def convert(
	elaboratable: ir.Fragment | ir.Elaboratable, name: str = 'top', platform = None, *, ports,
	emit_src: bool = True, strip_internal_attrs: bool = False, **kwargs
) -> str:

	fragment = ir.Fragment.get(elaboratable, platform).prepare(ports = ports, **kwargs)
	verilog_text, _ = convert_fragment(fragment, name, emit_src = emit_src, strip_internal_attrs = strip_internal_attrs)
	return verilog_text
