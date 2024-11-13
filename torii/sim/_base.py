# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable
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
	__slots__ = ()

	def __init__(self) -> None:
		self.reset()

	def reset(self) -> None:
		self.runnable = False
		self.passive  = True

	def run(self) -> None:
		raise NotImplementedError


class BaseSignalState:
	__slots__ = ()

	signal = NotImplemented

	curr = NotImplemented
	next = NotImplemented

	def set(self, value) -> None:
		raise NotImplementedError


class BaseSimulation:
	def reset(self) -> None:
		raise NotImplementedError

	def get_signal(self, signal) -> None:
		raise NotImplementedError

	slots = NotImplemented

	def add_trigger(self, process, signal, *, trigger = None):
		raise NotImplementedError

	def remove_trigger(self, process, signal):
		raise NotImplementedError

	def wait_interval(self, process, interval):
		raise NotImplementedError


class BaseEngine:
	def __init__(self, fragment: Fragment):
		pass

	def add_coroutine_process(self, process, *, default_cmd):
		raise NotImplementedError

	def add_clock_process(self, clock, *, phase, period):
		raise NotImplementedError

	def reset(self) -> None:
		raise NotImplementedError

	@property
	def now(self) -> int:
		raise NotImplementedError

	def advance(self) -> bool:
		raise NotImplementedError

	def write_vcd(
		self, *, vcd_file: IO | str | None, gtkw_file: IO | str | None = None,
		traces: Iterable[Signal]
	) -> None:
		raise NotImplementedError
