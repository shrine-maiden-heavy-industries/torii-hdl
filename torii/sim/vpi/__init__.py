# SPDX-License-Identifier: BSD-2-Clause

from typing    import Literal, TypeAlias

from ...hdl.ir import Fragment
from .._base   import BaseEngine

__all__ = (
	'VerilatorSimEngine',
	'VPIBackend',
	'VPISimEngine',
)

VPIBackend: TypeAlias = Literal['verilator']

class VPISimEngine(BaseEngine):

	def __init__(self, fragment: Fragment, *, vpi_backend: VPIBackend = 'verilator') -> None:
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

# TODO(aki): This might be able to be replaced with `functools.partial`
def VerilatorSimEngine(fragment: Fragment) -> VPISimEngine:
	return VPISimEngine(fragment = fragment, vpi_backend = 'verilator')
