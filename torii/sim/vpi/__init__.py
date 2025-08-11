# SPDX-License-Identifier: BSD-2-Clause

from typing    import Literal, TypeAlias

from ...hdl.ir import Fragment
from .._base   import BaseEngine, BaseSignalState, BaseSimulation

__all__ = (
	'VerilatorSimEngine',
	'VPIBackend',
	'VPISimEngine',
)

VPIBackend: TypeAlias = Literal['verilator']

class _VerilatorSignalState(BaseSignalState):
	pass

class _VerilatorSimulation(BaseSimulation):
	def __init__(self) -> None:
		pass

	def reset(self) -> None:
		pass

	def get_signal(self, signal) -> None:
		pass

	def add_trigger(self, process, signal, *, trigger=None):
		pass

	def remove_trigger(self, process, signal):
		pass

	def wait_interval(self, process, interval):
		pass

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
