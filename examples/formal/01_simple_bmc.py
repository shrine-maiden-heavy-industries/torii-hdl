# SPDX-License-Identifier: BSD-2-Clause

from torii                 import Elaboratable, Module, Signal, ClockDomain, ClockSignal
from torii.platform.formal import FormalPlatform
from torii.lib.formal      import Assert, Initial, Assume

class Counter(Elaboratable):
	def __init__(self, max_count: int, buggy: bool) -> None:
		self.max = max_count
		self.counter = Signal(16)
		self.clk = Signal(1)
		self.buggy = buggy

	def elaborate(self, _):
		m = Module()

		m.domains.sync = ClockDomain()
		m.d.comb += ClockSignal().eq(self.clk)
		if not self.buggy:
			with m.If(self.counter == self.max):
				m.d.sync += [ self.counter.eq(0) ]
			with m.Else():
				m.d.sync += [ self.counter.eq(self.counter + 1) ]
		else:
			m.d.sync += [ self.counter.eq(self.counter + 1) ]
		return m

	def formal(self, m: Module):
		with m.If(Initial()):
			m.d.comb += [ Assume(self.counter == 0) ]

		m.d.comb += [ Assert(self.counter <= self.max) ]
		return m


if __name__ == '__main__':
	dut_gold   = Counter(max_count = 8,   buggy = False)
	dut_buggy  = Counter(max_count = 8,   buggy = True)
	dut_sneaky = Counter(max_count = 800, buggy = True)

	print('DUT Gold - Will pass, should')
	FormalPlatform(mode = 'bmc').build(dut_gold, depth = 20, name = 'simple_bmc_gold')
	print('DUT Buggy - Won\'t pass, shouldn\'t')
	try:
		FormalPlatform(mode = 'bmc').build(dut_buggy, depth = 20, name = 'simple_bmc_buggy')
	except Exception as e:
		print(e)
	print('DUT Sneaky - Will pass, but shouldn\'t')
	FormalPlatform(mode = 'bmc').build(dut_sneaky, depth = 20, name = 'simple_bmc_sneaky')
