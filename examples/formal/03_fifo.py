# SPDX-License-Identifier: BSD-2-Clause
#
# This example takes the SyncFIFO from torii.lib.fifo and implements
# the formal verification tests found in the test suite for it, but all
# in a single Elaboratable.

from torii                 import (
	Elaboratable, Module, Signal, ClockDomain, ClockSignal, ResetSignal,
	Memory, Mux
)

from torii.platform.formal import FormalPlatform
from torii.lib.formal      import AnyConst, Past, Assume, Assert, Initial, Rose


class SyncFIFO(Elaboratable):
	def _incr(self, signal, modulo: int):
		if modulo == 2 ** len(signal):
			return signal + 1
		else:
			return Mux(signal == modulo - 1, 0, signal + 1)

	def __init__(self, *, width: int, depth: int, fwft: bool) -> None:
		if not isinstance(width, int) or width < 0:
			raise TypeError(f'FIFO width must be a non-negative integer, not {width!r}')

		if not isinstance(depth, int) or depth < 0:
			raise TypeError(f'FIFO depth must be a non-negative integer, not {depth!r}')

		self.width = width
		self.depth = depth
		self.fwft  = fwft

		self.w_data  = Signal(width, reset_less = True)
		self.w_rdy   = Signal() # writable; not full
		self.w_en    = Signal()
		self.w_level = Signal(range(depth + 1))

		self.r_data  = Signal(width, reset_less = True)
		self.r_rdy   = Signal() # readable; not empty
		self.r_en    = Signal()
		self.r_level = Signal(range(depth + 1))

		self.level = Signal(range(depth + 1))

		# For formal
		self.r_domain = 'sync'
		self.w_domain = 'sync'
		self.bound    = self.depth * 2 + 1

	def elaborate(self, _) -> Module:
		m = Module()

		if self.depth == 0:
			m.d.comb += [
				self.w_rdy.eq(0),
				self.r_rdy.eq(0),
			]
			return m

		m.d.comb += [
			self.w_rdy.eq(self.level != self.depth),
			self.r_rdy.eq(self.level != 0),
			self.w_level.eq(self.level),
			self.r_level.eq(self.level),
		]

		do_read  = self.r_rdy & self.r_en
		do_write = self.w_rdy & self.w_en

		m.submodules.storage = storage = Memory(width = self.width, depth = self.depth)
		w_port = storage.write_port()
		r_port = storage.read_port(
			domain = 'comb' if self.fwft else 'sync', transparent = self.fwft)
		self._produce = Signal(range(self.depth))
		self._consume = Signal(range(self.depth))

		m.d.comb += [
			w_port.addr.eq(self._produce),
			w_port.data.eq(self.w_data),
			w_port.en.eq(self.w_en & self.w_rdy),
		]
		with m.If(do_write):
			m.d.sync += self._produce.eq(self._incr(self._produce, self.depth))

		m.d.comb += [
			r_port.addr.eq(self._consume),
			self.r_data.eq(r_port.data),
		]
		if not self.fwft:
			m.d.comb += r_port.en.eq(self.r_en)
		with m.If(do_read):
			m.d.sync += self._consume.eq(self._incr(self._consume, self.depth))

		with m.If(do_write & ~do_read):
			m.d.sync += self.level.eq(self.level + 1)
		with m.If(do_read & ~do_write):
			m.d.sync += self.level.eq(self.level - 1)

		return m

	def formal(self, m) -> Module:

		m.domains += ClockDomain('sync')
		m.d.comb += ResetSignal().eq(0)
		if self.w_domain != 'sync':
			m.domains += ClockDomain(self.w_domain)
			m.d.comb += ResetSignal(self.w_domain).eq(0)
		if self.r_domain != 'sync':
			m.domains += ClockDomain(self.r_domain)
			m.d.comb += ResetSignal(self.r_domain).eq(0)

		with m.If(Initial()):
			m.d.comb += [
				Assume(self._produce < self.depth),
				Assume(self._consume < self.depth),
			]
			with m.If(self._produce == self._consume):
				m.d.comb += Assume((self.level == 0) | (self.level == self.depth))
			with m.If(self._produce > self._consume):
				m.d.comb += Assume(self.level == (self._produce - self._consume))
			with m.If(self._produce < self._consume):
				m.d.comb += Assume(self.level == (self.depth + self._produce - self._consume))
		with m.Else():
			m.d.comb += [
				Assert(self._produce < self.depth),
				Assert(self._consume < self.depth),
			]
			with m.If(self._produce == self._consume):
				m.d.comb += Assert((self.level == 0) | (self.level == self.depth))
			with m.If(self._produce > self._consume):
				m.d.comb += Assert(self.level == (self._produce - self._consume))
			with m.If(self._produce < self._consume):
				m.d.comb += Assert(self.level == (self.depth + self._produce - self._consume))

		entry_1 = AnyConst(self.width)
		entry_2 = AnyConst(self.width)

		with m.FSM(domain = self.w_domain) as write_fsm:
			with m.State('WRITE-1'):
				with m.If(self.w_rdy):
					m.d.comb += [
						self.w_data.eq(entry_1),
						self.w_en.eq(1)
					]
					m.next = 'WRITE-2'
			with m.State('WRITE-2'):
				with m.If(self.w_rdy):
					m.d.comb += [
						self.w_data.eq(entry_2),
						self.w_en.eq(1)
					]
					m.next = 'DONE'
			with m.State('DONE'):
				pass

		with m.FSM(domain = self.r_domain) as read_fsm:
			read_1 = Signal(self.width)
			read_2 = Signal(self.width)
			with m.State('READ'):
				m.d.comb += self.r_en.eq(1)
				if self.fwft:
					r_rdy = self.r_rdy
				else:
					r_rdy = Past(self.r_rdy, domain = self.r_domain)
				with m.If(r_rdy):
					m.d.sync += [
						read_1.eq(read_2),
						read_2.eq(self.r_data),
					]
				with m.If((read_1 == entry_1) & (read_2 == entry_2)):
					m.next = 'DONE'
			with m.State('DONE'):
				pass

		with m.If(Initial()):
			m.d.comb += Assume(write_fsm.ongoing('WRITE-1'))
			m.d.comb += Assume(read_fsm.ongoing('READ'))
		with m.If(Past(Initial(), self.bound - 1)):
			m.d.comb += Assert(read_fsm.ongoing('DONE'))

		with m.If(ResetSignal(domain = self.w_domain)):
			m.d.comb += Assert(~self.r_rdy)

		if self.w_domain != 'sync' or self.r_domain != 'sync':
			m.d.comb += Assume(
				Rose(ClockSignal(self.w_domain)) |
				Rose(ClockSignal(self.r_domain))
			)

		return m

if __name__ == '__main__':
	dut = SyncFIFO(width = 8, depth = 4, fwft = True)

	FormalPlatform(mode = 'bmc').build(dut, depth = dut.bound, name = 'syncfifo', multiclock = "on", wait = "on")
