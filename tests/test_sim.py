# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

import os
from contextlib    import contextmanager

from torii.util    import flatten
from torii.hdl.ast import *
from torii.hdl.cd  import *
from torii.hdl.mem import *
from torii.hdl.rec import *
from torii.hdl.dsl import *
from torii.hdl.ir  import *
from torii.sim     import *

from .utils        import *

class SimulatorUnitTestCase(FHDLTestCase):
	def assertStatement(self, stmt, inputs, output, reset = 0):
		inputs = [Value.cast(i) for i in inputs]
		output = Value.cast(output)

		isigs = [ Signal(i.shape(), name = n) for i, n in zip(inputs, 'abcd') ]
		osig  = Signal(output.shape(), name = 'y', reset = reset)

		stmt = stmt(osig, *isigs)
		frag = Fragment()
		frag.add_statements(stmt)
		for signal in flatten(s._lhs_signals() for s in Statement.cast(stmt)):
			frag.add_driver(signal)

		sim = Simulator(frag)

		def process():
			for isig, input in zip(isigs, inputs):
				yield isig.eq(input)
			yield Settle()
			self.assertEqual((yield osig), output.value)

		sim.add_process(process)
		with sim.write_vcd('test.vcd', 'test.gtkw', traces = [ *isigs, osig ]):
			sim.run()

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

	def test_repl(self):
		self.assertStatement(
			lambda y, a: y.eq(Repl(a, 3)),
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


class SimulatorIntegrationTestCase(FHDLTestCase):
	@contextmanager
	def assertSimulation(self, module, deadline = None):
		sim = Simulator(module)
		yield sim
		with sim.write_vcd('test.vcd', 'test.gtkw'):
			if deadline is None:
				sim.run()
			else:
				sim.run_until(deadline)

	def setUp_counter(self):
		self.count = Signal(3, reset = 4)
		self.sync  = ClockDomain()

		self.m = Module()
		self.m.d.sync  += self.count.eq(self.count + 1)
		self.m.domains += self.sync

	def test_counter_process(self):
		self.setUp_counter()
		with self.assertSimulation(self.m) as sim:

			def process():
				self.assertEqual((yield self.count), 4)
				yield Delay(1e-6)
				self.assertEqual((yield self.count), 4)
				yield self.sync.clk.eq(1)
				self.assertEqual((yield self.count), 4)
				yield Settle()
				self.assertEqual((yield self.count), 5)
				yield Delay(1e-6)
				self.assertEqual((yield self.count), 5)
				yield self.sync.clk.eq(0)
				self.assertEqual((yield self.count), 5)
				yield Settle()
				self.assertEqual((yield self.count), 5)
				for _ in range(3):
					yield Delay(1e-6)
					yield self.sync.clk.eq(1)
					yield Delay(1e-6)
					yield self.sync.clk.eq(0)
				self.assertEqual((yield self.count), 0)

			sim.add_process(process)

	def test_counter_clock_and_sync_process(self):
		self.setUp_counter()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6, domain = 'sync')

			def process():
				self.assertEqual((yield self.count), 4)
				self.assertEqual((yield self.sync.clk), 1)
				yield
				self.assertEqual((yield self.count), 5)
				self.assertEqual((yield self.sync.clk), 1)
				for _ in range(3):
					yield
				self.assertEqual((yield self.count), 0)

			sim.add_sync_process(process)

	def test_reset(self):
		self.setUp_counter()
		sim = Simulator(self.m)
		sim.add_clock(1e-6)
		times = 0

		def process():
			nonlocal times
			self.assertEqual((yield self.count), 4)
			yield
			self.assertEqual((yield self.count), 5)
			yield
			self.assertEqual((yield self.count), 6)
			yield
			times += 1

		sim.add_sync_process(process)
		sim.run()
		sim.reset()
		sim.run()
		self.assertEqual(times, 2)

	def setUp_alu(self):
		self.a = Signal(8)
		self.b = Signal(8)
		self.o = Signal(8)
		self.x = Signal(8)
		self.s = Signal(2)
		self.sync = ClockDomain(reset_less = True)

		self.m = Module()
		self.m.d.comb += self.x.eq(self.a ^ self.b)
		with self.m.Switch(self.s):
			with self.m.Case(0):
				self.m.d.sync += self.o.eq(self.a + self.b)
			with self.m.Case(1):
				self.m.d.sync += self.o.eq(self.a - self.b)
			with self.m.Case():
				self.m.d.sync += self.o.eq(0)
		self.m.domains += self.sync

	def test_alu(self):
		self.setUp_alu()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6)

			def process():
				yield self.a.eq(5)
				yield self.b.eq(1)
				yield
				self.assertEqual((yield self.x), 4)
				yield
				self.assertEqual((yield self.o), 6)
				yield self.s.eq(1)
				yield
				yield
				self.assertEqual((yield self.o), 4)
				yield self.s.eq(2)
				yield
				yield
				self.assertEqual((yield self.o), 0)

			sim.add_sync_process(process)

	def setUp_clock_phase(self):
		self.m = Module()
		self.phase0 = self.m.domains.phase0 = ClockDomain()
		self.phase90 = self.m.domains.phase90 = ClockDomain()
		self.phase180 = self.m.domains.phase180 = ClockDomain()
		self.phase270 = self.m.domains.phase270 = ClockDomain()
		self.check = self.m.domains.check = ClockDomain()

		self.expected = [
			[0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
			[0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1],
			[0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1],
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
		]

	def test_clock_phase(self):
		self.setUp_clock_phase()
		with self.assertSimulation(self.m) as sim:
			period = 1
			sim.add_clock(period/8, phase = 0,          domain = 'check')
			sim.add_clock(period,   phase = 0*period/4, domain = 'phase0')
			sim.add_clock(period,   phase = 1*period/4, domain = 'phase90')
			sim.add_clock(period,   phase = 2*period/4, domain = 'phase180')
			sim.add_clock(period,   phase = 3*period/4, domain = 'phase270')

			def proc():
				clocks = [
					self.phase0.clk,
					self.phase90.clk,
					self.phase180.clk,
					self.phase270.clk
				]
				for i in range(16):
					yield
					for j, c in enumerate(clocks):
						self.assertEqual((yield c), self.expected[j][i])

			sim.add_sync_process(proc, domain = 'check')

	def setUp_multiclock(self):
		self.sys = ClockDomain()
		self.pix = ClockDomain()

		self.m = Module()
		self.m.domains += self.sys, self.pix

	def test_multiclock(self):
		self.setUp_multiclock()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6, domain = 'sys')
			sim.add_clock(0.3e-6, domain = 'pix')

			def sys_process():
				yield Passive()
				yield
				yield
				self.fail()

			def pix_process():
				yield
				yield
				yield

			sim.add_sync_process(sys_process, domain = 'sys')
			sim.add_sync_process(pix_process, domain = 'pix')

	def setUp_lhs_rhs(self):
		self.i = Signal(8)
		self.o = Signal(8)

		self.m = Module()
		self.m.d.comb += self.o.eq(self.i)

	def test_complex_lhs_rhs(self):
		self.setUp_lhs_rhs()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.i.eq(0b10101010)
				yield self.i[:4].eq(-1)
				yield Settle()
				self.assertEqual((yield self.i[:4]), 0b1111)
				self.assertEqual((yield self.i), 0b10101111)
			sim.add_process(process)

	def test_run_until(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertSimulation(m, deadline = 100e-6) as sim:
			sim.add_clock(1e-6)

			def process():
				for _ in range(101):
					yield Delay(1e-6)
				self.fail()
			sim.add_process(process)

	def test_run_until_fail(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertRaises(AssertionError):
			with self.assertSimulation(m, deadline = 100e-6) as sim:
				sim.add_clock(1e-6)

				def process():
					for _ in range(99):
						yield Delay(1e-6)
					self.fail()
				sim.add_process(process)

	def test_add_process_wrong(self):
		with self.assertSimulation(Module()) as sim:
			with self.assertRaisesRegex(
				TypeError,
				r'^Cannot add a process 1 because it is not a generator function$'
			):
				sim.add_process(1)

	def test_add_process_wrong_generator(self):
		with self.assertSimulation(Module()) as sim:
			with self.assertRaisesRegex(
				TypeError,
				r'^Cannot add a process <.+?> because it is not a generator function$'
			):
				def process():
					yield Delay()
				sim.add_process(process())

	def test_add_clock_wrong_twice(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertSimulation(m) as sim:
			sim.add_clock(1)
			with self.assertRaisesRegex(
				ValueError,
				r'^Domain \'sync\' already has a clock driving it$'
			):
				sim.add_clock(1)

	def test_add_clock_wrong_missing(self):
		m = Module()
		with self.assertSimulation(m) as sim:
			with self.assertRaisesRegex(
				ValueError,
				r'^Domain \'sync\' is not present in simulation$'
			):
				sim.add_clock(1)

	def test_add_clock_if_exists(self):
		m = Module()
		with self.assertSimulation(m) as sim:
			sim.add_clock(1, if_exists = True)

	def test_command_wrong(self):
		survived = False
		with self.assertSimulation(Module()) as sim:
			def process():
				nonlocal survived
				with self.assertRaisesRegex(
					TypeError,
					r'Received unsupported command 1 from process .+?'
				):
					yield 1
				yield Settle()
				survived = True
			sim.add_process(process)
		self.assertTrue(survived)

	def setUp_memory(self, rd_synchronous = True, rd_transparent = True, wr_granularity = None):
		self.m = Module()
		self.memory = Memory(width = 8, depth = 4, init = [0xaa, 0x55])
		self.m.submodules.rdport = self.rdport = self.memory.read_port(
			domain = 'sync' if rd_synchronous else 'comb',
			transparent = rd_transparent
		)
		self.m.submodules.wrport = self.wrport = self.memory.write_port(
			granularity = wr_granularity
		)

	def test_memory_init(self):
		self.setUp_memory()
		with self.assertSimulation(self.m) as sim:
			def process():
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.rdport.addr.eq(1)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x55)
				yield self.rdport.addr.eq(2)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x00)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write(self):
		self.setUp_memory()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.addr.eq(4)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				yield self.wrport.en.eq(0)
				yield self.rdport.addr.eq(4)
				yield
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write_granularity(self):
		self.setUp_memory(wr_granularity = 4)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x50)
				yield self.wrport.en.eq(0b00)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.wrport.en.eq(0b10)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0x5a)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(0b01)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0x53)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_read_before_write(self):
		self.setUp_memory(rd_transparent = False)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write_through(self):
		self.setUp_memory(rd_transparent = True)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
				yield
				yield self.rdport.addr.eq(1)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_async_read_write(self):
		self.setUp_memory(rd_synchronous = False)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.rdport.addr.eq(0)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.rdport.addr.eq(1)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x55)
				yield self.rdport.addr.eq(0)
				yield self.wrport.addr.eq(0)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield Tick('sync')
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_process(process)

	def test_memory_read_only(self):
		self.m = Module()
		self.memory = Memory(width = 8, depth = 4, init = [0xaa, 0x55])
		self.m.submodules.rdport = self.rdport = self.memory.read_port()
		with self.assertSimulation(self.m) as sim:
			def process():
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.rdport.addr.eq(1)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x55)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_sample_helpers(self):
		m = Module()
		s = Signal(2)

		def mk(x):
			y = Signal.like(x)
			m.d.comb += y.eq(x)
			return y

		p0, r0, f0, s0 = mk(Past(s, 0)), mk(Rose(s)),    mk(Fell(s)),    mk(Stable(s))
		p1, r1, f1, s1 = mk(Past(s)),    mk(Rose(s, 1)), mk(Fell(s, 1)), mk(Stable(s, 1))
		p2, r2, f2, s2 = mk(Past(s, 2)), mk(Rose(s, 2)), mk(Fell(s, 2)), mk(Stable(s, 2))
		p3, r3, f3, s3 = mk(Past(s, 3)), mk(Rose(s, 3)), mk(Fell(s, 3)), mk(Stable(s, 3))
		with self.assertSimulation(m) as sim:
			def process_gen():
				yield s.eq(0b10)
				yield
				yield
				yield s.eq(0b01)
				yield

			def process_check():
				yield
				yield
				yield

				self.assertEqual((yield p0), 0b01)
				self.assertEqual((yield p1), 0b10)
				self.assertEqual((yield p2), 0b10)
				self.assertEqual((yield p3), 0b00)

				self.assertEqual((yield s0), 0b0)
				self.assertEqual((yield s1), 0b1)
				self.assertEqual((yield s2), 0b0)
				self.assertEqual((yield s3), 0b1)

				self.assertEqual((yield r0), 0b01)
				self.assertEqual((yield r1), 0b00)
				self.assertEqual((yield r2), 0b10)
				self.assertEqual((yield r3), 0b00)

				self.assertEqual((yield f0), 0b10)
				self.assertEqual((yield f1), 0b00)
				self.assertEqual((yield f2), 0b00)
				self.assertEqual((yield f3), 0b00)
			sim.add_clock(1e-6)
			sim.add_sync_process(process_gen)
			sim.add_sync_process(process_check)

	def test_vcd_wrong_nonzero_time(self):
		s = Signal()
		m = Module()
		m.d.sync += s.eq(s)
		sim = Simulator(m)
		sim.add_clock(1e-6)
		sim.run_until(1e-5)
		with self.assertRaisesRegex(
			ValueError,
			r'^Cannot start writing waveforms after advancing simulation time$'
		):
			with open(os.path.devnull, 'w') as f:
				with sim.write_vcd(f):
					pass


class SimulatorRegressionTestCase(FHDLTestCase):
	def test_bug_325(self):
		dut = Module()
		dut.d.comb += Signal().eq(Cat())
		Simulator(dut).run()

	def test_bug_325_bis(self):
		dut = Module()
		dut.d.comb += Signal().eq(Repl(Const(1), 0))
		Simulator(dut).run()

	def test_bug_473(self):
		sim = Simulator(Module())

		def process():
			self.assertEqual((yield -(Const(0b11, 2).as_signed())), 1)
		sim.add_process(process)
		sim.run()

	def test_bug_595(self):
		dut = Module()
		with dut.FSM(name = 'name with space'):
			with dut.State(0):
				pass
		sim = Simulator(dut)
		with self.assertRaisesRegex(
			NameError,
			r'^Signal \'bench\.top\.name with space_state\' contains a whitespace character$'
		):
			with open(os.path.devnull, 'w') as f:
				with sim.write_vcd(f):
					sim.run()

	def test_bug_588(self):
		dut = Module()
		a = Signal(32)
		b = Signal(32)
		z = Signal(32)
		dut.d.comb += z.eq(a << b)
		with self.assertRaisesRegex(
			OverflowError,
			r'^Value defined at .+?/test_sim\.py:\d+ is 4294967327 bits wide, '
			r'which is unlikely to simulate in reasonable time$'
		):
			Simulator(dut)

	def test_bug_566(self):
		dut = Module()
		dut.d.sync += Signal().eq(0)
		sim = Simulator(dut)
		with self.assertWarnsRegex(
			UserWarning,
			r'^Adding a clock process that drives a clock domain object named \'sync\', '
			r'which is distinct from an identically named domain in the simulated design$'
		):
			sim.add_clock(1e-6, domain = ClockDomain('sync'))
