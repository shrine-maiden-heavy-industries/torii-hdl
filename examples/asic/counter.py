# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl                  import Elaboratable, Signal, Module
from torii.build                import Resource, Clock, Pins
from torii.platform.asic.sky130 import Sky130BHighDensityPlatform

class Counter(Elaboratable):
	def __init__(self, width: int):
		self.v = Signal(width, reset = 2**width - 1)
		self.o = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.sync += self.v.eq(self.v + 1)
		m.d.comb += self.o.eq(self.v[-1])
		return m

class ExampleFlow(Sky130BHighDensityPlatform):
	default_clk  = 'clk'

	flow_settings = {
		'FP_CORE_UTIL': 1,
		'DESIGN_IS_CORE': 0,
	}

	connectors = ()
	resources  = (
		Resource('clk', 0, Pins('C', dir = 'i'), Clock(1e6)),
	)

if __name__ == '__main__':
	ctr = Counter(width = 16)
	flow = ExampleFlow()

	flow.build(ctr, name = 'ctr', ports = [ctr.o])
