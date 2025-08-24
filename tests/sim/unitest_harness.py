# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl.ast   import Array, Cat, Const, Mux, Signal, signed, unsigned
from torii.hdl.rec   import Record

from ._harness_types import SimulatorUnitTestMixinBase

class SimulatorUnitTestsMixin(SimulatorUnitTestMixinBase):

	def test_invert(self):
		self.assertStatement(
			lambda y, a: y.eq(~a),
			[Const(0b0000, 4)], Const(0b1111, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(~a),
			[Const(0b1010, 4)], Const(0b0101, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(~a),
			[Const(0, 4)], Const(-1, 4)
		)

	def test_neg(self):
		self.assertStatement(
			lambda y, a: y.eq(-a),
			[Const(0b0000, 4)], Const(0b0000, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(-a),
			[Const(0b0001, 4)], Const(0b1111, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(-a),
			[Const(0b1010, 4)], Const(0b0110, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(-a),
			[Const(1, 4)], Const(-1, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(-a),
			[Const(5, 4)], Const(-5, 4)
		)

	def test_bool(self):
		self.assertStatement(
			lambda y, a: y.eq(a.bool()),
			[Const(0, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.bool()),
			[Const(1, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.bool()),
			[Const(2, 4)], Const(1)
		)

	def test_as_unsigned(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a.as_unsigned() == b),
			[Const(0b01, signed(2)), Const(0b0001, unsigned(4))], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.as_unsigned() == b),
			[Const(0b11, signed(2)), Const(0b0011, unsigned(4))], Const(1)
		)

	def test_as_unsigned_lhs(self):
		self.assertStatement(
			lambda y, a: y.as_unsigned().eq(a),
			[Const(0b01, unsigned(2))], Const(0b0001, signed(4))
		)

	def test_as_signed(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a.as_signed() == b),
			[Const(0b01, unsigned(2)), Const(0b0001, signed(4))], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.as_signed() == b),
			[Const(0b11, unsigned(2)), Const(0b1111, signed(4))], Const(1)
		)

	def test_as_signed_issue_502(self):
		self.assertStatement(
			lambda y, a: y.eq(a.as_signed()),
			[Const(0b01, unsigned(2))], Const(0b0001, signed(4))
		)
		self.assertStatement(
			lambda y, a: y.eq(a.as_signed()),
			[Const(0b11, unsigned(2))], Const(0b1111, signed(4))
		)

	def test_as_signed_lhs(self):
		self.assertStatement(
			lambda y, a: y.as_signed().eq(a),
			[Const(0b01, unsigned(2))], Const(0b0001, signed(4))
		)

	def test_any(self):
		self.assertStatement(
			lambda y, a: y.eq(a.any()),
			[Const(0b00, 2)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.any()),
			[Const(0b01, 2)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.any()),
			[Const(0b10, 2)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.any()),
			[Const(0b11, 2)], Const(1)
		)

	def test_all(self):
		self.assertStatement(
			lambda y, a: y.eq(a.all()),
			[Const(0b00, 2)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.all()),
			[Const(0b01, 2)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.all()),
			[Const(0b10, 2)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.all()),
			[Const(0b11, 2)], Const(1)
		)

	def test_xor_unary(self):
		self.assertStatement(
			lambda y, a: y.eq(a.xor()),
			[Const(0b00, 2)], Const(0)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.xor()),
			[Const(0b01, 2)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.xor()),
			[Const(0b10, 2)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.xor()),
			[Const(0b11, 2)], Const(0)
		)

	def test_add(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a + b),
			[Const(0,  4), Const(1, 4)], Const(1,   4)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a + b),
			[Const(-5, 4), Const(-5, 4)], Const(-10, 5)
		)

	def test_sub(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a - b),
			[Const(2, 4), Const(1, 4)], Const(1,   4)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a - b),
			[Const(0, 4), Const(1, 4)], Const(-1,  4)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a - b),
			[Const(0, 4), Const(10, 4)], Const(-10, 5)
		)

	def test_mul(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a * b),
			[Const(2, 4), Const(1, 4)], Const(2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a * b),
			[Const(2, 4), Const(2, 4)], Const(4, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a * b),
			[Const(7, 4), Const(7, 4)], Const(49, 8)
		)

	def test_floordiv(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(2, 4), Const(1, 4)], Const(2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(2, 4), Const(2, 4)], Const(1, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(7, 4), Const(2, 4)], Const(3, 8)
		)

	def test_floordiv_neg(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(-5, 4), Const(2, 4)], Const(-3, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(-5, 4), Const(-2, 4)], Const(2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(5, 4), Const(2, 4)], Const(2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a // b),
			[Const(5, 4), Const(-2, 4)], Const(-3, 8)
		)

	def test_mod(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(2, 4), Const(0, 4)], Const(0, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(2, 4), Const(1, 4)], Const(0, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(2, 4), Const(2, 4)], Const(0, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(7, 4), Const(2, 4)], Const(1, 8)
		)

	def test_mod_neg(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(-5, 4), Const(3, 4)], Const(1, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(-5, 4), Const(-3, 4)], Const(-2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(5, 4), Const(3, 4)], Const(2, 8)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a % b),
			[Const(5, 4), Const(-3, 4)], Const(-1, 8)
		)

	def test_and(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a & b),
			[Const(0b1100, 4), Const(0b1010, 4)], Const(0b1000, 4)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a & b),
			[Const(0b1010, 4), Const(0b10, signed(2))], Const(0b1010, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(a),
			[Const(0b1010, 4) & Const(-2, 2).as_unsigned()], Const(0b0010, 4)
		)

	def test_or(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a | b),
			[Const(0b1100, 4), Const(0b1010, 4)], Const(0b1110, 4)
		)

	def test_xor_binary(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a ^ b),
			[Const(0b1100, 4), Const(0b1010, 4)], Const(0b0110, 4)
		)

	def test_shl(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a << b),
			[Const(0b1001, 4), Const(0)],  Const(0b1001, 5)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a << b),
			[Const(0b1001, 4), Const(3)],  Const(0b1001000, 7)
		)

	def test_shr(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a >> b),
			[Const(0b1001, 4), Const(0)],  Const(0b1001, 4)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a >> b),
			[Const(0b1001, 4), Const(2)],  Const(0b10,  4)
		)

	def test_eq(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a == b),
			[Const(0, 4), Const(0, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a == b),
			[Const(0, 4), Const(1, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a == b),
			[Const(1, 4), Const(0, 4)], Const(0)
		)

	def test_ne(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a != b),
			[Const(0, 4), Const(0, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a != b),
			[Const(0, 4), Const(1, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a != b),
			[Const(1, 4), Const(0, 4)], Const(1)
		)

	def test_lt(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a < b),
			[Const(0, 4), Const(0, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a < b),
			[Const(0, 4), Const(1, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a < b),
			[Const(1, 4), Const(0, 4)], Const(0)
		)

	def test_ge(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a >= b),
			[Const(0, 4), Const(0, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a >= b),
			[Const(0, 4), Const(1, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a >= b),
			[Const(1, 4), Const(0, 4)], Const(1)
		)

	def test_gt(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a > b),
			[Const(0, 4), Const(0, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a > b),
			[Const(0, 4), Const(1, 4)], Const(0)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a > b),
			[Const(1, 4), Const(0, 4)], Const(1)
		)

	def test_le(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a <= b),
			[Const(0, 4), Const(0, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a <= b),
			[Const(0, 4), Const(1, 4)], Const(1)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a <= b),
			[Const(1, 4), Const(0, 4)], Const(0)
		)

	def test_mux(self):
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(c, a, b)),
			[Const(2, 4), Const(3, 4), Const(0)], Const(3, 4)
		)
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(c, a, b)),
			[Const(2, 4), Const(3, 4), Const(1)], Const(2, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(a),
			[Mux(0, Const(0b1010, 4), Const(0b10, 2).as_signed())], Const(0b1110, 4)
		)
		self.assertStatement(
			lambda y, a: y.eq(a),
			[Mux(0, Const(0b1010, 4), Const(-2, 2).as_unsigned())], Const(0b0010, 4)
		)

	def test_mux_invert(self):
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(~c, a, b)),
			[Const(2, 4), Const(3, 4), Const(0)], Const(2, 4)
		)
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(~c, a, b)),
			[Const(2, 4), Const(3, 4), Const(1)], Const(3, 4)
		)

	def test_mux_wide(self):
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(c, a, b)),
			[Const(2, 4), Const(3, 4), Const(0, 2)], Const(3, 4)
		)
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(c, a, b)),
			[Const(2, 4), Const(3, 4), Const(1, 2)], Const(2, 4)
		)
		self.assertStatement(
			lambda y, a, b, c: y.eq(Mux(c, a, b)),
			[Const(2, 4), Const(3, 4), Const(2, 2)], Const(2, 4)
		)

	def test_abs(self):
		self.assertStatement(
			lambda y, a: y.eq(abs(a)),
			[Const(3,  unsigned(8))], Const(3, unsigned(8))
		)
		self.assertStatement(
			lambda y, a: y.eq(abs(a)),
			[Const(-3, unsigned(8))], Const(-3, unsigned(8))
		)
		self.assertStatement(
			lambda y, a: y.eq(abs(a)),
			[Const(3,  signed(8))], Const(3, signed(8))
		)
		self.assertStatement(
			lambda y, a: y.eq(abs(a)),
			[Const(-3, signed(8))], Const(3, signed(8))
		)

	def test_slice(self):
		self.assertStatement(
			lambda y, a: y.eq(a[2]),
			[Const(0b10110100, 8)], Const(0b1,  1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a[2:4]),
			[Const(0b10110100, 8)], Const(0b01, 2)
		)

	def test_slice_lhs(self):
		self.assertStatement(
			lambda y, a: y[2].eq(a),
			[Const(0b0,  1)], Const(0b11111011, 8),
			reset = 0b11111111
		)
		self.assertStatement(
			lambda y, a: y[2:4].eq(a),
			[Const(0b01, 2)], Const(0b11110111, 8),
			reset = 0b11111011
		)

	def test_bit_select(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a.bit_select(b, 3)),
			[Const(0b10110100, 8), Const(0)], Const(0b100, 3)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.bit_select(b, 3)),
			[Const(0b10110100, 8), Const(2)], Const(0b101, 3)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.bit_select(b, 3)),
			[Const(0b10110100, 8), Const(3)], Const(0b110, 3)
		)

	def test_bit_select_lhs(self):
		self.assertStatement(
			lambda y, a, b: y.bit_select(a, 3).eq(b),
			[Const(0), Const(0b100, 3)], Const(0b11111100, 8),
			reset = 0b11111111
		)
		self.assertStatement(
			lambda y, a, b: y.bit_select(a, 3).eq(b),
			[Const(2), Const(0b101, 3)], Const(0b11110111, 8),
			reset = 0b11111111
		)
		self.assertStatement(
			lambda y, a, b: y.bit_select(a, 3).eq(b),
			[Const(3), Const(0b110, 3)], Const(0b11110111, 8),
			reset = 0b11111111
		)

	def test_word_select(self):
		self.assertStatement(
			lambda y, a, b: y.eq(a.word_select(b, 3)),
			[Const(0b10110100, 8), Const(0)], Const(0b100, 3)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.word_select(b, 3)),
			[Const(0b10110100, 8), Const(1)], Const(0b110, 3)
		)
		self.assertStatement(
			lambda y, a, b: y.eq(a.word_select(b, 3)),
			[Const(0b10110100, 8), Const(2)], Const(0b010, 3)
		)

	def test_word_select_lhs(self):
		self.assertStatement(
			lambda y, a, b: y.word_select(a, 3).eq(b),
			[Const(0), Const(0b100, 3)], Const(0b11111100, 8), reset = 0b11111111
		)
		self.assertStatement(
			lambda y, a, b: y.word_select(a, 3).eq(b),
			[Const(1), Const(0b101, 3)], Const(0b11101111, 8), reset = 0b11111111
		)
		self.assertStatement(
			lambda y, a, b: y.word_select(a, 3).eq(b),
			[Const(2), Const(0b110, 3)], Const(0b10111111, 8), reset = 0b11111111
		)

	def test_cat(self):
		self.assertStatement(
			lambda y, *xs: y.eq(Cat(*xs)),
			[Const(0b10, 2), Const(0b01, 2)], Const(0b0110, 4)
		)

	def test_cat_lhs(self):
		l = Signal(3) # noqa: E741
		m = Signal(3) # noqa: E741
		n = Signal(3) # noqa: E741
		self.assertStatement(
			lambda y, a: [Cat(l, m, n).eq(a), y.eq(Cat(n, m, l))],
			[Const(0b100101110, 9)], Const(0b110101100, 9)
		)

	def test_nested_cat_lhs(self):
		l = Signal(3) # noqa: E741
		m = Signal(3) # noqa: E741
		n = Signal(3) # noqa: E741
		self.assertStatement(
			lambda y, a: [Cat(Cat(l, Cat(m)), n).eq(a), y.eq(Cat(n, m, l))],
			[Const(0b100101110, 9)], Const(0b110101100, 9)
		)

	def test_record(self):
		rec = Record([
			('l', 1),
			('m', 2),
		])
		self.assertStatement(
			lambda y, a: [rec.eq(a), y.eq(rec)],
			[Const(0b101, 3)], Const(0b101, 3)
		)

	def test_replicate(self):
		self.assertStatement(
			lambda y, a: y.eq(a.replicate(3)),
			[Const(0b10, 2)], Const(0b101010, 6)
		)

	def test_array(self):
		array = Array([1, 4, 10])
		self.assertStatement(
			lambda y, a: y.eq(array[a]),
			[Const(0)], Const(1)
		)
		self.assertStatement(
			lambda y, a: y.eq(array[a]),
			[Const(1)], Const(4)
		)
		self.assertStatement(
			lambda y, a: y.eq(array[a]),
			[Const(2)], Const(10)
		)

	def test_array_oob(self):
		array = Array([1, 4, 10])
		self.assertStatement(
			lambda y, a: y.eq(array[a]),
			[Const(3)], Const(10)
		)
		self.assertStatement(
			lambda y, a: y.eq(array[a]),
			[Const(4)], Const(10)
		)

	def test_array_lhs(self):
		l = Signal(3, reset = 1) # noqa: E741
		m = Signal(3, reset = 4) # noqa: E741
		n = Signal(3, reset = 7) # noqa: E741

		array = Array([l, m, n])
		self.assertStatement(
			lambda y, a, b: [array[a].eq(b), y.eq(Cat(*array))],
			[Const(0), Const(0b000)], Const(0b111100000)
		)
		self.assertStatement(
			lambda y, a, b: [array[a].eq(b), y.eq(Cat(*array))],
			[Const(1), Const(0b010)], Const(0b111010001)
		)
		self.assertStatement(
			lambda y, a, b: [array[a].eq(b), y.eq(Cat(*array))],
			[Const(2), Const(0b100)], Const(0b100100001)
		)

	def test_array_lhs_oob(self):
		l = Signal(3) # noqa: E741
		m = Signal(3) # noqa: E741
		n = Signal(3) # noqa: E741
		array = Array([l, m, n])
		self.assertStatement(
			lambda y, a, b: [array[a].eq(b), y.eq(Cat(*array))],
			[Const(3), Const(0b001)], Const(0b001000000)
		)
		self.assertStatement(
			lambda y, a, b: [array[a].eq(b), y.eq(Cat(*array))],
			[Const(4), Const(0b010)], Const(0b010000000)
		)

	def test_array_index(self):
		array = Array(Array(x * y for y in range(10)) for x in range(10))
		for x in range(10):
			for y in range(10):
				self.assertStatement(
					lambda y, a, b: y.eq(array[a][b]),
					[Const(x), Const(y)], Const(x * y)
				)

	def test_array_attr(self):
		from collections import namedtuple
		pair = namedtuple('pair', ('p', 'n'))

		array = Array(pair(x, -x) for x in range(10))
		for i in range(10):
			self.assertStatement(
				lambda y, a: y.eq(array[a].p + array[a].n),
				[Const(i)], Const(0)
			)

	def test_shift_left(self):
		self.assertStatement(
			lambda y, a: y.eq(a.shift_left(1)),
			[Const(0b10100010, 8)], Const(   0b101000100, 9)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.shift_left(4)),
			[Const(0b10100010, 8)], Const(0b101000100000, 12)
		)

	def test_shift_right(self):
		self.assertStatement(
			lambda y, a: y.eq(a.shift_right(1)),
			[Const(0b10100010, 8)], Const(0b1010001, 7)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.shift_right(4)),
			[Const(0b10100010, 8)], Const(   0b1010, 4)
		)

	def test_rotate_left(self):
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(1)),
			[Const(0b1)], Const(0b1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(1)),
			[Const(0b1001000)], Const(0b0010001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(5)),
			[Const(0b1000000)], Const(0b0010000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(5)),
			[Const(0b1000001)], Const(0b0110000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(7)),
			[Const(0b1000000)], Const(0b1000000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(7)),
			[Const(0b1000001)], Const(0b1000001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(9)),
			[Const(0b1000000)], Const(0b0000010)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(9)),
			[Const(0b1000001)], Const(0b0000110)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-1)),
			[Const(0b1)], Const(0b1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-1)),
			[Const(0b1001000)], Const(0b0100100)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-5)),
			[Const(0b1000000)], Const(0b0000010)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-5)),
			[Const(0b1000001)], Const(0b0000110)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-7)),
			[Const(0b1000000)], Const(0b1000000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-7)),
			[Const(0b1000001)], Const(0b1000001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-9)),
			[Const(0b1000000)], Const(0b0010000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_left(-9)),
			[Const(0b1000001)], Const(0b0110000)
		)

	def test_rotate_right(self):

		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(1)),
			[Const(0b1)], Const(0b1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(1)),
			[Const(0b1001000)], Const(0b0100100)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(5)),
			[Const(0b1000000)], Const(0b0000010)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(5)),
			[Const(0b1000001)], Const(0b0000110)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(7)),
			[Const(0b1000000)], Const(0b1000000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(7)),
			[Const(0b1000001)], Const(0b1000001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(9)),
			[Const(0b1000000)], Const(0b0010000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(9)),
			[Const(0b1000001)], Const(0b0110000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-1)),
			[Const(0b1)], Const(0b1)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-1)),
			[Const(0b1001000)], Const(0b0010001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-5)),
			[Const(0b1000000)], Const(0b0010000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-5)),
			[Const(0b1000001)], Const(0b0110000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-7)),
			[Const(0b1000000)], Const(0b1000000)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-7)),
			[Const(0b1000001)], Const(0b1000001)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-9)),
			[Const(0b1000000)], Const(0b0000010)
		)
		self.assertStatement(
			lambda y, a: y.eq(a.rotate_right(-9)),
			[Const(0b1000001)], Const(0b0000110)
		)
