# SPDX-License-Identifier: BSD-2-Clause

import warnings

from collections.abc import Iterable

from ..hdl.ir     import Elaboratable
from ..hdl.dsl    import Module
from ..hdl.ast    import Signal
from ..util.units import bits_for

__all__ = (
	'PRBS',
)


# def calculate_polynomial(bits: Iterable[int], len: int) -> int:
#
# 	acc = 0
# 	for bit in bits:
# 		acc |= 1 << bit
#
# 	mask = 0
# 	for bit_num in range(len + 1):
# 		mask |= 1 << bit_num
#
# 	return acc & mask

class PRBS(Elaboratable):
	'''
	An LFSR-based Pseudorandom Binary Sequence generator



	Some common PRBS Sequence polynomials are listed below:

	* PRBS-7 - :math:`x^7+x^6+1` - `0x??`
	* PRBS-9 - :math:`x^9+x^5+1` - `0x???`
	* PRBS-11 - :math:`x^11+x^9+1` - `0x???`
	* PRBS-13 - :math:`x^13+x^12+x^2+x+1` - `0x????`
	* PRBS-15 - :math:`x^15+x^14+1` - `0x????`
	* PRBS-20 - :math:`x^20+x^3+1` - `0x?????`
	* PRBS-23 - :math:`x^23+x^18+1` - `0x??????`
	* PRBS-31 - :math:`x^31+x^28+1` - `0x????????`

	Attributes
	----------
	state : Signal[width]
		The current state of the LFSR.

	out : Signal[1]
		The bit-serial output of the PRBS.

		This is equivalent to using the last bit of the ``state`` parameter

	Parameters
	----------
	polynomial : int
		The LFSR Polynomial to use for the PRBS.

	width : int
		How many bits wide the LFSR is.

	seed : int
		The initial starting seed value for the LFSR.

	'''

	def __init__(self, *, polynomial: int, width: int, seed: int) -> None:

		# Clip the seed so it fits into our LFSR
		seed_width = bits_for(seed)
		if seed_width > width:
			warnings.warn(
				f'The seed value of {seed:X} is too wide for the PRBS of width {width} ({seed_width} > {width})'
				' and will be truncated.',
				RuntimeWarning, stacklevel = 2
			)

		self._polynomial = polynomial
		self._width      = width
		self._seed       = seed

		self.output = Signal(width, reset = seed)

	def elaborate(self, platform) -> Module:
		m = Module()


		return m
