# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl     import Module, Signal
from torii.back    import verilog
from torii.lib.cdc import FFSynchronizer

i, o = Signal(name = 'i'), Signal(name = 'o')
m = Module()
m.submodules += FFSynchronizer(i, o)

if __name__ == '__main__':
	print(verilog.convert(m, ports = [i, o]))
