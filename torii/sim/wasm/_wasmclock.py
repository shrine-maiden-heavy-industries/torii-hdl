# SPDX-License-Identifier: BSD-2-Clause

from .._base import BaseProcess

__all__ = (
	'WASMClockProcess',
)

class WASMClockProcess(BaseProcess):
	def __init__(self, state, signal, *, phase, period) -> None:
		if len(signal) != 1:
			raise TypeError(f'Clock signal must be exactly 1-wide, not {len(signal)}')

		self.state  = state
		self.slot   = self.state.get_signal(signal)
		self.phase  = phase
		self.period = period

		self.reset()

	def reset(self):
		self.runnable = True
		self.passive = True

		self.initial = True

	def run(self):
		self.runnable = False

		if self.initial:
			self.initial = False
			self.state.wait_interval(self, self.phase)

		else:
			clk_state = self.state.slots[self.slot]
			clk_state.set(not clk_state.curr.get())
			self.state.wait_interval(self, self.period // 2)
