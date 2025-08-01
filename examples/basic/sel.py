# SPDX-License-Identifier: BSD-2-Clause

from torii.back import verilog
from torii.hdl  import Elaboratable, Module, Record, Signal

class FlatGPIO(Elaboratable):
	def __init__(self, pins, bus) -> None:
		self.pins = pins
		self.bus  = bus

	def elaborate(self, platform) -> Module:
		bus  = self.bus

		m = Module()
		m.d.comb += bus.r_data.eq(self.pins.word_select(bus.addr, len(bus.r_data)))
		with m.If(bus.we):
			m.d.sync += self.pins.word_select(bus.addr, len(bus.w_data)).eq(bus.w_data)
		return m

if __name__ == '__main__':
	bus = Record([
		('addr',   3),
		('r_data', 2),
		('w_data', 2),
		('we',     1),
	])
	pins = Signal(8)
	gpio = FlatGPIO(pins, bus)

	print(verilog.convert(gpio, ports = [pins, bus.addr, bus.r_data, bus.w_data, bus.we]))
