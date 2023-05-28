# SPDX-License-Identifier: BSD-2-Clause

from torii         import Signal, Module
from torii.lib.cdc import FFSynchronizer
from torii.back    import verilog


i, o = Signal(name = 'i'), Signal(name = 'o')
m = Module()
m.submodules += FFSynchronizer(i, o)

if __name__ == '__main__':
	print(verilog.convert(m, ports = [i, o]))
