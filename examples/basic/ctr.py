# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl  import Elaboratable, Module, Signal
from torii.back import verilog

class Counter(Elaboratable):
	def __init__(self, width: int):
		self.v = Signal(width, reset = 2**width-1)
		self.o = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.sync += self.v.eq(self.v + 1)
		m.d.comb += self.o.eq(self.v[-1])
		return m

ctr = Counter(width = 16)
if __name__ == '__main__':
	print(verilog.convert(ctr, ports = [ctr.o]))
