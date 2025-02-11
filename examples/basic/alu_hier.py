# SPDX-License-Identifier: BSD-2-Clause

from torii      import Elaboratable, Module, Signal
from torii.back import verilog

class Adder(Elaboratable):
	def __init__(self, width: int):
		self.a   = Signal(width)
		self.b   = Signal(width)
		self.o   = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.comb += self.o.eq(self.a + self.b)
		return m


class Subtractor(Elaboratable):
	def __init__(self, width: int):
		self.a   = Signal(width)
		self.b   = Signal(width)
		self.o   = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.comb += self.o.eq(self.a - self.b)
		return m


class ALU(Elaboratable):
	def __init__(self, width: int):
		self.op  = Signal()
		self.a   = Signal(width)
		self.b   = Signal(width)
		self.o   = Signal(width)

		self.add = Adder(width)
		self.sub = Subtractor(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		m.submodules.add = self.add
		m.submodules.sub = self.sub
		m.d.comb += [
			self.add.a.eq(self.a),
			self.sub.a.eq(self.a),
			self.add.b.eq(self.b),
			self.sub.b.eq(self.b),
		]
		with m.If(self.op):
			m.d.comb += self.o.eq(self.sub.o)
		with m.Else():
			m.d.comb += self.o.eq(self.add.o)
		return m


if __name__ == '__main__':
	alu = ALU(width = 16)

	print(verilog.convert(alu, ports = [alu.op, alu.a, alu.b, alu.o]))
