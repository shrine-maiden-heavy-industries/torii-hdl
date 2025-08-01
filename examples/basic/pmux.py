# SPDX-License-Identifier: BSD-2-Clause

from torii.back import verilog
from torii.hdl  import Elaboratable, Module, Signal

class ParMux(Elaboratable):
	def __init__(self, width) -> None:
		self.s = Signal(3)
		self.a = Signal(width)
		self.b = Signal(width)
		self.c = Signal(width)
		self.o = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		with m.Switch(self.s):
			with m.Case('--1'):
				m.d.comb += self.o.eq(self.a)
			with m.Case('-1-'):
				m.d.comb += self.o.eq(self.b)
			with m.Case('1--'):
				m.d.comb += self.o.eq(self.c)
			with m.Default():
				m.d.comb += self.o.eq(0)
		return m

if __name__ == '__main__':
	pmux = ParMux(width = 16)

	print(verilog.convert(pmux, ports = [pmux.s, pmux.a, pmux.b, pmux.c, pmux.o]))
