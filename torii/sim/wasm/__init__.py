# SPDX-License-Identifier: BSD-2-Clause

from ...hdl.ir import Fragment
from .._base   import BaseEngine

from ._wasmrtl import _WASMFragmentCompiler

__all__ = (
	'WASMSimEngine',
)

class WASMSimEngine(BaseEngine):
	def __init__(self, fragment: Fragment) -> None:
		self._frag = fragment
		self._processed = _WASMFragmentCompiler(None)(self._frag)

	def add_coroutine_process(self, process, *, default_cmd):
		pass

	def add_clock_process(self, clock, *, phase, period):
		pass

	def reset(self):
		pass

	def advance(self):
		return True

	@property
	def now(self):
		return 0
