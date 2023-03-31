# SPDX-License-Identifier: BSD-2-Clause

from ...      import Elaboratable, Module, Signal
from .one_hot import Decoder as OneHotDecoder

__all__ = (
	'Decoder',
	'Encoder',
)


class Encoder(Elaboratable):
	'''
	Priority encode requests to binary.

	If any bit in ``i`` is asserted, ``n`` is low and ``o`` indicates the least significant
	asserted bit.
	Otherwise, ``n`` is high and ``o`` is ``0``.

	Parameters
	----------
	width : int
		Bit width of the input.

	Attributes
	----------
	i : Signal(width), in
		Input requests.
	o : Signal(range(width)), out
		Encoded natural binary.
	n : Signal, out
		Invalid: no input bits are asserted.

	'''

	def __init__(self, width: int) -> None:
		self.width = width

		self.i = Signal(width)
		self.o = Signal(range(width))
		self.n = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		for j in reversed(range(self.width)):
			with m.If(self.i[j]):
				m.d.comb += self.o.eq(j)
		m.d.comb += self.n.eq(self.i == 0)
		return m


class Decoder(OneHotDecoder):
	'''
	Decode binary to priority request.

	Identical to :py:class:`torii.lib.coding.one_hot.Decoder`.

	'''
