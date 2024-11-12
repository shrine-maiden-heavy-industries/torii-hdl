# SPDX-License-Identifier: BSD-2-Clause

from ..hdl.ast     import SignalDict
from ..tools.yosys import YosysError, find_yosys
from .             import rtlil

__all__ = (
	'convert_fragment',
	'convert',
	'YosysError',
)

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


def convert_fragment(*args, black_boxes: dict[str, str] | None = None, **kwargs) -> tuple[str, SignalDict]:
	rtlil_text, name_map = rtlil.convert_fragment(*args, **kwargs)
	return (_convert_rtlil_text(rtlil_text, black_boxes, src_loc_at = 1), name_map)


def convert(*args, black_boxes: dict[str, str] | None = None, **kwargs) -> str:
	rtlil_text = rtlil.convert(*args, **kwargs)
	return _convert_rtlil_text(rtlil_text, black_boxes, src_loc_at = 1)
