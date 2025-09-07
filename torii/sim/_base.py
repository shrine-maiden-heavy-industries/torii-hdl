# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Generator, Iterable
from contextlib      import contextmanager
from typing          import IO

from ..hdl           import Signal
from ..hdl.ir        import Fragment

__all__ = (
	'BaseEngine',
	'BaseProcess',
	'BaseSignalState',
	'BaseSimulation',
)

class BaseProcess:
	'''
	.. todo:: Document Me
	'''

	__slots__ = ()

	def __init__(self) -> None:
		self.reset()

	def reset(self) -> None:
		'''
		.. todo:: Document Me
		'''

		self.runnable = False
		self.passive  = True

	def run(self) -> None:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

class BaseSignalState:
	'''
	.. todo:: Document Me
	'''

	__slots__ = ()

	signal = NotImplemented
	''' .. todo:: Document Me '''

	curr = NotImplemented
	''' .. todo:: Document Me '''

	next = NotImplemented
	''' .. todo:: Document Me '''

	def set(self, value) -> None:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

class BaseSimulation:
	'''
	.. todo:: Document Me
	'''

	def reset(self) -> None:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def get_signal(self, signal) -> None:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	slots = NotImplemented
	''' .. todo:: Document Me '''

	def add_trigger(self, process, signal, *, trigger = None):
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def remove_trigger(self, process, signal):
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def wait_interval(self, process, interval):
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

class BaseEngine:
	'''
	.. todo:: Document Me
	'''

	def __init__(self, fragment: Fragment) -> None:
		pass

	def add_coroutine_process(self, process, *, default_cmd):
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def add_clock_process(self, clock, *, phase, period):
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def reset(self) -> None:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	@property
	def now(self) -> int:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	def advance(self) -> bool:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError

	@contextmanager
	def write_vcd(
		self, *, vcd_file: IO | str | None, gtkw_file: IO | str | None = None,
		traces: Iterable[Signal]
	) -> Generator[None, None, None]:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError
