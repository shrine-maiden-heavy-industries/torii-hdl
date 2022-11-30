# SPDX-License-Identifier: BSD-2-Clause

from torii         import Signal, Module
from torii.lib.cdc import FFSynchronizer
from torii.cli     import main


i, o = Signal(name = 'i'), Signal(name = 'o')
m = Module()
m.submodules += FFSynchronizer(i, o)

if __name__ == '__main__':
	main(m, ports = [i, o])
