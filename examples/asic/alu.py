# SPDX-License-Identifier: BSD-2-Clause

from torii                      import Elaboratable, Module, Signal, Cat
from torii.platform.asic.sky130 import Sky130BHighDensityPlatform

class ALU(Elaboratable):
	def __init__(self, width: int):
		self.sel = Signal(2)
		self.a   = Signal(width)
		self.b   = Signal(width)
		self.o   = Signal(width)
		self.co  = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		with m.If(self.sel == 0b00):
			m.d.comb += self.o.eq(self.a | self.b)
		with m.Elif(self.sel == 0b01):
			m.d.comb += self.o.eq(self.a & self.b)
		with m.Elif(self.sel == 0b10):
			m.d.comb += self.o.eq(self.a ^ self.b)
		with m.Else():
			m.d.comb += Cat(self.o, self.co).eq(self.a - self.b)
		return m

class ExampleFlow(Sky130BHighDensityPlatform):
	flow_settings = {
		'DESIGN_IS_CORE': 0,
	}
	connectors = ()
	resources  = ()

if __name__ == '__main__':
	alu = ALU(width = 16)
	flow = ExampleFlow()

	flow.build(alu, name = 'alu', ports = [alu.sel, alu.a, alu.b, alu.o, alu.co])
