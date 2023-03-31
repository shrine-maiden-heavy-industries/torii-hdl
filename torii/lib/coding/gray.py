# SPDX-License-Identifier: BSD-2-Clause

from ... import Const, Elaboratable, Module, Signal

__all__ = (
	'Decoder',
	'Encoder',
)

class Encoder(Elaboratable):
	'''
	Encode binary to Gray code.

	Parameters
	----------
	width : int
		Bit width.

	Attributes
	----------
	i : Signal(width), in
		Natural binary input.
	o : Signal(width), out
		Encoded Gray code.

	'''

	def __init__(self, width: int) -> None:
		self.width = width

		self.i = Signal(width)
		self.o = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		m.d.comb += self.o.eq(self.i ^ self.i[1:])
		return m


class Decoder(Elaboratable):
	'''
	Decode Gray code to binary.

	Parameters
	----------
	width : int
		Bit width.

	Attributes
	----------
	i : Signal(width), in
		Gray code input.
	o : Signal(width), out
		Decoded natural binary.

	'''

	def __init__(self, width: int) -> None:
		self.width = width

		self.i = Signal(width)
		self.o = Signal(width)

	def elaborate(self, platform) -> Module:
		m = Module()
		rhs = Const(0)
		for i in reversed(range(self.width)):
			rhs = rhs ^ self.i[i]
			m.d.comb += self.o[i].eq(rhs)
		return m
