# SPDX-License-Identifier: BSD-2-Clause
# If the design does not create a "sync" clock domain, it is created by the Torii build system
# using the platform default clock (and default reset, if any).

from torii                                     import Elaboratable, Signal, Module
from torii_boards.lattice.ice40_hx1k_blink_evn import ICE40HX1KBlinkEVNPlatform

class Blinky(Elaboratable):
	def elaborate(self, platform) -> Module:
		led   = platform.request('led', 0)
		timer = Signal(20)

		m = Module()
		m.d.sync += timer.eq(timer + 1)
		m.d.comb += led.o.eq(timer[-1])
		return m


if __name__ == '__main__':
	platform = ICE40HX1KBlinkEVNPlatform()
	platform.build(Blinky(), do_program = True)
