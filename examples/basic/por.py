# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl  import ClockDomain, ClockSignal, Module, ResetSignal, Signal
from torii.back import verilog

m = Module()
cd_por  = ClockDomain(reset_less = True)
cd_sync = ClockDomain()
m.domains += cd_por, cd_sync

delay = Signal(range(256), reset = 255)
with m.If(delay != 0):
	m.d.por += delay.eq(delay - 1)
m.d.comb += [
	ClockSignal().eq(cd_por.clk),
	ResetSignal().eq(delay != 0),
]

if __name__ == '__main__':
	print(verilog.convert(m, ports = [cd_por.clk]))
