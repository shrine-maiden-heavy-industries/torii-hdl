# SPDX-License-Identifier: BSD-2-Clause

from ... import Elaboratable, Module, Signal

__all__ = (
	'Decoder',
	'Encoder',
)

class Encoder(Elaboratable):
	'''
	Encode one-hot to binary.

	If one bit in ``i`` is asserted, ``n`` is low and ``o`` indicates the asserted bit.
	Otherwise, ``n`` is high and ``o`` is ``0``.

	Parameters
	----------
	width : int
		Bit width of the input

	Attributes
	----------
	i : Signal(width), in
		One-hot input.
	o : Signal(range(width)), out
		Encoded natural binary.
	n : Signal, out
		Invalid: either none or multiple input bits are asserted.

	'''

	def __init__(self, width: int) -> None:
		self.width = width

		self.i = Signal(width)
		self.o = Signal(range(width))
		self.n = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		with m.Switch(self.i):
			for j in range(self.width):
				with m.Case(1 << j):
					m.d.comb += self.o.eq(j)
			with m.Default():
				m.d.comb += self.n.eq(1)
		return m

class Decoder(Elaboratable):
	'''
	Decode binary to one-hot.

	If ``n`` is low, only the ``i``-th bit in ``o`` is asserted.
	If ``n`` is high, ``o`` is ``0``.

	Parameters
	----------
	width : int
		Bit width of the output.

	Attributes
	----------
	i : Signal(range(width)), in
		Input binary.
	o : Signal(width), out
		Decoded one-hot.
	n : Signal, in
		Invalid, no output bits are to be asserted.

	'''

	def __init__(self, width: int) -> None:
		self.width = width

		self.i = Signal(range(width))
		self.n = Signal()
		self.o = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		with m.Switch(self.i):
			for j in range(len(self.o)):
				with m.Case(j):
					m.d.comb += self.o.eq(1 << j)
		with m.If(self.n):
			m.d.comb += self.o.eq(0)
		return m
