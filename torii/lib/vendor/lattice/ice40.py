# SPDX-License-Identifier: BSD-2-Clause

from ....hdl import Elaboratable, Module, Instance, Signal

__all__ = (
	'ice40Warmboot',
)

class ice40Warmboot(Elaboratable):
	''' Lattice ice40 Warmboot block

	Attributes
	----------

	boot_sel : Signal(2)
		boot slot selection

	boot_strb: Signal
		Strobe to trigger warmboot

	'''

	def __init__(self) -> None:
		self.boot_sel  = Signal(2)
		self.boot_strb = Signal()

	def elaborate(self, _) -> Module:
		m = Module()

		m.submodules.ice40_warmboot = Instance(
			'SB_WARMBOOT',
			i_BOOT = self.boot_strb,
			i_S0   = self.boot_sel[0],
			i_S1   = self.boot_sel[1]
		)

		return m
