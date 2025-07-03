# SPDX-License-Identifier: BSD-2-Clause

from ...hdl.ir          import Fragment
from .._base            import BaseEngine

__all__ = (
	'VerilatorEngine',
)

class VerilatorEngine(BaseEngine):

	def __init__(self, fragment: Fragment) -> None:
		self._frag = fragment

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
