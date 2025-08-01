# SPDX-License-Identifier: BSD-2-Clause

from torii.back import verilog
from torii.hdl  import Elaboratable, Module, Signal

class Counter(Elaboratable):
	def __init__(self, width: int) -> None:
		self.v = Signal(width, reset = 2**width - 1)
		self.o = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.sync += self.v.eq(self.v + 1)
		m.d.comb += self.o.eq(self.v[-1])
		return m

ctr = Counter(width = 16)
if __name__ == '__main__':
	print(verilog.convert(ctr, ports = [ctr.o]))
