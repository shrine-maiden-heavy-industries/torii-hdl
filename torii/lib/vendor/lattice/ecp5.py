# SPDX-License-Identifier: BSD-2-Clause

'''
This module provides wrapper modules for lattice ECP5 primitive blocks.

'''

from ....build.plat import Platform
from ....hdl.dsl    import Module
from ....hdl.ir     import Elaboratable, Instance

__all__ = (

)

class PRADD18A(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'PRADD18A'
		)

		return m

class PRADD9A(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'PRADD9A'
		)

		return m

class MUX161(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MUX161'
		)

		return m

class MUX21(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MUX21'
		)

		return m

class MUX321(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MUX321'
		)

		return m

class MUX41(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MUX41'
		)

		return m

class MUX81(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MUX81'
		)

		return m

class MULT18X18C(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MULT18X18C'
		)

		return m

class MULT18X18D(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MULT18X18D'
		)

		return m

class MULT9X9C(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MULT9X9C'
		)

		return m

class MULT9X9D(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'MULT9X9D'
		)

		return m


class CLKDIVF(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'CLKDIVF'
		)

		return m

class DCCA(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DCCA'
		)

		return m

class DCSC(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DCSC'
		)

		return m

class DLLDELD(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DLLDELD'
		)

		return m

class ECLKBRIDGESCS(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'ECLKBRIDGESCS'
		)

		return m

class EHXPLLL(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'EHXPLLL'
		)

		return m

class PLLREFCS(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'PLLREFCS'
		)

		return m

class DDRDLLA(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DDRDLLA'
		)

		return m

class DQSBUFM(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DQSBUFM'
		)

		return m

class ECLKSYNCB(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'ECLKSYNCB'
		)

		return m

class DELAYF(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DELAYF'
		)

		return m

class DELAYG(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DELAYG'
		)

		return m

class DTR(Elaboratable):
	'''

	'''

	def __init__(self) -> None:
		pass

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.submodules += Instance(
			'DTR'
		)

		return m
