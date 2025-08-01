# SPDX-License-Identifier: BSD-2-Clause

from torii.back import verilog
from torii.hdl  import Array, Elaboratable, Module, Record, Signal

class GPIO(Elaboratable):
	def __init__(self, pins, bus) -> None:
		self.pins = pins
		self.bus  = bus

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.comb += self.bus.r_data.eq(self.pins[self.bus.addr])
		with m.If(self.bus.we):
			m.d.sync += self.pins[self.bus.addr].eq(self.bus.w_data)
		return m

if __name__ == '__main__':
	bus = Record([
		('addr',   3),
		('r_data', 1),
		('w_data', 1),
		('we',     1),
	])
	pins = Signal(8)
	gpio = GPIO(Array(pins), bus)

	print(verilog.convert(gpio, ports = [pins, bus.addr, bus.r_data, bus.w_data, bus.we]))
