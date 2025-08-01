# SPDX-License-Identifier: BSD-2-Clause

import warnings
from enum          import Enum, EnumMeta
from sys           import version_info

from torii.hdl.ast import (
	Array, Cat, ClockSignal, Const, Edge, Fell, Initial, Mux, Part, Past, ResetSignal, Rose, Sample,
	Shape, ShapeCastable, ShapeLike, Signal, Slice, Stable, Switch, Value, ValueCastable, ValueLike,
	signed, unsigned,
)
from torii.hdl.cd  import ClockDomain
from torii.hdl.dsl import Module
from torii.hdl.ir  import Elaboratable
from torii.sim     import Delay, Simulator, Tick


from ..utils       import ToriiTestSuiteCase

class UnsignedEnum(Enum):
	FOO = 1
	BAR = 2
	BAZ = 3

class SignedEnum(Enum):
	FOO = -1
	BAR = 0
	BAZ = +1

class StringEnum(Enum):
	FOO = 'a'
	BAR = 'b'

class TypedEnum(int, Enum):
	FOO = 1
	BAR = 2
	BAZ = 3

class ShapeTestCase(ToriiTestSuiteCase):
	def test_make(self):
		s1 = Shape()
		self.assertEqual(s1.width, 1)
		self.assertEqual(s1.signed, False)
		s2 = Shape(signed = True)
		self.assertEqual(s2.width, 1)
		self.assertEqual(s2.signed, True)
		s3 = Shape(3, True)
		self.assertEqual(s3.width, 3)
		self.assertEqual(s3.signed, True)
		s4 = Shape(0)
		self.assertEqual(s4.width, 0)
		self.assertEqual(s4.signed, False)

	def test_make_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Width must be an integer, not \'a\'$'
		):
			Shape('a')
		with self.assertRaisesRegex(
			ValueError,
			r'^Width of an unsigned value must be zero or a positive integer, not -1$'
		):
			Shape(-1, signed = False)
		with self.assertRaisesRegex(
			ValueError,
			r'^Width of a signed value must be a positive integer, not 0$'
		):
			Shape(0, signed = True)

	def test_compare_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Shapes may be compared with shape-castable objects, not \'hi\'$'
		):
			Shape(1, True) == 'hi'

	def test_compare_tuple_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Shapes may be compared with shape-castable objects, not \(2, 3\)$'
		):
			Shape(1, True) == (2, 3)

	def test_repr(self):
		self.assertEqual(repr(Shape()), 'unsigned(1)')
		self.assertEqual(repr(Shape(2, True)), 'signed(2)')

	def test_convert_tuple_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^cannot unpack non-iterable Shape object$'
		):
			width, signed = Shape()

	def test_unsigned(self):
		s1 = unsigned(2)
		self.assertIsInstance(s1, Shape)
		self.assertEqual(s1.width, 2)
		self.assertEqual(s1.signed, False)

	def test_signed(self):
		s1 = signed(2)
		self.assertIsInstance(s1, Shape)
		self.assertEqual(s1.width, 2)
		self.assertEqual(s1.signed, True)

	def test_cast_shape(self):
		s1 = Shape.cast(unsigned(1))
		self.assertEqual(s1.width, 1)
		self.assertEqual(s1.signed, False)
		s2 = Shape.cast(signed(3))
		self.assertEqual(s2.width, 3)
		self.assertEqual(s2.signed, True)

	def test_cast_int(self):
		s1 = Shape.cast(2)
		self.assertEqual(s1.width, 2)
		self.assertEqual(s1.signed, False)

	def test_cast_int_wrong(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Width of an unsigned value must be zero or a positive integer, not -1$'
		):
			Shape.cast(-1)

	def test_cast_tuple_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Object \(-1, True\) cannot be converted to a Torii shape$'
		):
			Shape.cast((-1, True))

	def test_cast_range(self):
		s1 = Shape.cast(range(0, 8))
		self.assertEqual(s1.width, 3)
		self.assertEqual(s1.signed, False)
		s2 = Shape.cast(range(0, 9))
		self.assertEqual(s2.width, 4)
		self.assertEqual(s2.signed, False)
		s3 = Shape.cast(range(-7, 8))
		self.assertEqual(s3.width, 4)
		self.assertEqual(s3.signed, True)
		s4 = Shape.cast(range(0, 1))
		self.assertEqual(s4.width, 0)
		self.assertEqual(s4.signed, False)
		s5 = Shape.cast(range(-1, 0))
		self.assertEqual(s5.width, 1)
		self.assertEqual(s5.signed, True)
		s6 = Shape.cast(range(0, 0))
		self.assertEqual(s6.width, 0)
		self.assertEqual(s6.signed, False)
		s7 = Shape.cast(range(-1, -1))
		self.assertEqual(s7.width, 0)
		self.assertEqual(s7.signed, False)
		s8 = Shape.cast(range(0, 10, 3))
		self.assertEqual(s8.width, 4)
		self.assertEqual(s8.signed, False)
		s9 = Shape.cast(range(0, 3, 3))
		self.assertEqual(s9.width, 0)
		self.assertEqual(s9.signed, False)

	def test_cast_enum(self):
		s1 = Shape.cast(UnsignedEnum)
		self.assertEqual(s1.width, 2)
		self.assertEqual(s1.signed, False)
		s2 = Shape.cast(SignedEnum)
		self.assertEqual(s2.width, 2)
		self.assertEqual(s2.signed, True)

	def test_cast_enum_bad(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Only enumerations whose members have constant-castable values can be used in Torii code$'
		):
			Shape.cast(StringEnum)

	def test_cast_bad(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Object \'foo\' cannot be converted to a Torii shape$'
		):
			Shape.cast('foo')

class MockShapeCastable(ShapeCastable):
	def __init__(self, dest) -> None:
		self.dest = dest

	def as_shape(self):
		return self.dest

	def const(self, obj):
		return Const(obj, self.dest)

class ShapeCastableTestCase(ToriiTestSuiteCase):
	def test_no_override(self):
		# NOTE(aki): Seems like the wording changed in 3.12
		if version_info >= (3, 12):
			err_msg_regex = r'^Can\'t instantiate abstract class MockShapeCastableNoOverride without an implementation'
			r'for abstract methods \'as_shape\', \'const\'$'
		else:
			err_msg_regex = r'^Can\'t instantiate abstract class MockShapeCastableNoOverride with abstract methods '
			r'\'as_shape\', \'const\'$'

		with self.assertRaisesRegex(TypeError, err_msg_regex):
			class MockShapeCastableNoOverride(ShapeCastable):
				def __init__(self) -> None:
					pass # :nocov:

			_ = MockShapeCastableNoOverride()

	def test_cast(self):
		sc = MockShapeCastable(unsigned(2))
		self.assertEqual(Shape.cast(sc), unsigned(2))

	def test_recurse_bad(self):
		sc = MockShapeCastable(None)
		sc.dest = sc
		with self.assertRaisesRegex(
			RecursionError,
			r'^Shape-castable object <.+> casts to itself$'
		):
			Shape.cast(sc)

	def test_recurse(self):
		sc = MockShapeCastable(MockShapeCastable(unsigned(1)))
		self.assertEqual(Shape.cast(sc), unsigned(1))

class ShapeLikeTestCase(ToriiTestSuiteCase):
	def test_construct(self):
		with self.assertRaises(TypeError):
			ShapeLike()

	def test_subclass(self):
		self.assertTrue(issubclass(Shape, ShapeLike))
		self.assertTrue(issubclass(MockShapeCastable, ShapeLike))
		self.assertTrue(issubclass(int, ShapeLike))
		self.assertTrue(issubclass(range, ShapeLike))
		self.assertTrue(issubclass(EnumMeta, ShapeLike))
		self.assertFalse(issubclass(Enum, ShapeLike))
		self.assertFalse(issubclass(str, ShapeLike))
		self.assertTrue(issubclass(ShapeLike, ShapeLike))

	def test_isinstance(self):
		self.assertTrue(isinstance(unsigned(2), ShapeLike))
		self.assertTrue(isinstance(MockShapeCastable(unsigned(2)), ShapeLike))
		self.assertTrue(isinstance(2, ShapeLike))
		self.assertTrue(isinstance(0, ShapeLike))
		self.assertFalse(isinstance(-1, ShapeLike))
		self.assertTrue(isinstance(range(10), ShapeLike))
		self.assertFalse(isinstance('abc', ShapeLike))

	def test_isinstance_enum(self):
		class EnumA(Enum):
			A = 1
			B = 2

		class EnumB(Enum):
			A = 'a'
			B = 'b'

		class EnumC(Enum):
			A = Cat(Const(1, 2), Const(0, 2))

		self.assertTrue(isinstance(EnumA, ShapeLike))
		self.assertFalse(isinstance(EnumB, ShapeLike))
		self.assertTrue(isinstance(EnumC, ShapeLike))

class ValueTestCase(ToriiTestSuiteCase):
	def test_cast(self):
		self.assertIsInstance(Value.cast(0), Const)
		self.assertIsInstance(Value.cast(True), Const)
		c = Const(0)
		self.assertIs(Value.cast(c), c)
		with self.assertRaisesRegex(
			TypeError,
			r'^Object \'str\' cannot be converted to a Torii value$'
		):
			Value.cast('str')

	def test_cast_enum(self):
		e1 = Value.cast(UnsignedEnum.FOO)
		self.assertIsInstance(e1, Const)
		self.assertEqual(e1.shape(), unsigned(2))
		e2 = Value.cast(SignedEnum.FOO)
		self.assertIsInstance(e2, Const)
		self.assertEqual(e2.shape(), signed(2))

	def test_cast_typedenum(self):
		e1 = Value.cast(TypedEnum.FOO)
		self.assertIsInstance(e1, Const)
		self.assertEqual(e1.shape(), unsigned(2))

	def test_cast_enum_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Only enumerations whose members have constant-castable values can be used in Torii code$'
		):
			Value.cast(StringEnum.FOO)

	def test_bool(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Attempted to convert Torii value to Python boolean$'
		):
			if Const(0):
				pass

	def test_len(self):
		self.assertEqual(len(Const(10)), 4)

	def test_getitem_int(self):
		s1 = Const(10)[0]
		self.assertIsInstance(s1, Slice)
		self.assertEqual(s1.start, 0)
		self.assertEqual(s1.stop, 1)
		s2 = Const(10)[-1]
		self.assertIsInstance(s2, Slice)
		self.assertEqual(s2.start, 3)
		self.assertEqual(s2.stop, 4)
		with self.assertRaisesRegex(
			IndexError,
			r'^Index 5 is out of bounds for a 4-bit value$'
		):
			Const(10)[5]

	def test_getitem_slice(self):
		s1 = Const(10)[1:3]
		self.assertIsInstance(s1, Slice)
		self.assertEqual(s1.start, 1)
		self.assertEqual(s1.stop, 3)
		s2 = Const(10)[1:-2]
		self.assertIsInstance(s2, Slice)
		self.assertEqual(s2.start, 1)
		self.assertEqual(s2.stop, 2)
		s3 = Const(31)[::2]
		self.assertIsInstance(s3, Cat)
		self.assertIsInstance(s3.parts[0], Slice)
		self.assertEqual(s3.parts[0].start, 0)
		self.assertEqual(s3.parts[0].stop, 1)
		self.assertIsInstance(s3.parts[1], Slice)
		self.assertEqual(s3.parts[1].start, 2)
		self.assertEqual(s3.parts[1].stop, 3)
		self.assertIsInstance(s3.parts[2], Slice)
		self.assertEqual(s3.parts[2].start, 4)
		self.assertEqual(s3.parts[2].stop, 5)

	def test_getitem_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Cannot index value with \'str\'$'
		):
			Const(31)['str']

		with self.assertRaises(
			SyntaxError,
			msg = 'Slicing a value with a Value is unsupported, use `Value.bit_select()` or `Value.word_select()` instead.' # noqa: E501
		):
			Const(31)[Signal(3)]

		s = Signal(3)
		with self.assertRaises(
			SyntaxError,
			msg = 'Indexing a value with another value is not supported, use `Value.bit_select()` instead.'
		):
			Const(31)[s:s + 3]

	def test_shift_left(self):
		self.assertRepr(
			Const(256, unsigned(9)).shift_left(0),
			'(cat (const 0\'d0) (const 9\'d256))'
		)

		self.assertRepr(
			Const(256, unsigned(9)).shift_left(1),
			'(cat (const 1\'d0) (const 9\'d256))'
		)
		self.assertRepr(
			Const(256, unsigned(9)).shift_left(5),
			'(cat (const 5\'d0) (const 9\'d256))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_left(1),
			'(s (cat (const 1\'d0) (const 9\'sd-256)))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_left(5),
			'(s (cat (const 5\'d0) (const 9\'sd-256)))'
		)

		self.assertRepr(
			Const(256, unsigned(9)).shift_left(-1),
			'(slice (const 9\'d256) 1:9)'
		)
		self.assertRepr(
			Const(256, unsigned(9)).shift_left(-5),
			'(slice (const 9\'d256) 5:9)'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_left(-1),
			'(s (slice (const 9\'sd-256) 1:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_left(-5),
			'(s (slice (const 9\'sd-256) 5:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_left(-15),
			'(s (slice (const 9\'sd-256) 8:9))'
		)

	def test_shift_left_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Shift amount must be an integer, not \'str\'$'
		):
			Const(31).shift_left('str')

	def test_shift_right(self):
		self.assertRepr(
			Const(256, unsigned(9)).shift_right(0),
			'(slice (const 9\'d256) 0:9)'
		)

		self.assertRepr(
			Const(256, unsigned(9)).shift_right(-1),
			'(cat (const 1\'d0) (const 9\'d256))'
		)
		self.assertRepr(
			Const(256, unsigned(9)).shift_right(-5),
			'(cat (const 5\'d0) (const 9\'d256))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(-1),
			'(s (cat (const 1\'d0) (const 9\'sd-256)))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(-5),
			'(s (cat (const 5\'d0) (const 9\'sd-256)))'
		)

		self.assertRepr(
			Const(256, unsigned(9)).shift_right(1),
			'(slice (const 9\'d256) 1:9)'
		)
		self.assertRepr(
			Const(256, unsigned(9)).shift_right(5),
			'(slice (const 9\'d256) 5:9)'
		)
		self.assertRepr(
			Const(256, unsigned(9)).shift_right(15),
			'(slice (const 9\'d256) 9:9)'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(1),
			'(s (slice (const 9\'sd-256) 1:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(5),
			'(s (slice (const 9\'sd-256) 5:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(7),
			'(s (slice (const 9\'sd-256) 7:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(8),
			'(s (slice (const 9\'sd-256) 8:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(9),
			'(s (slice (const 9\'sd-256) 8:9))'
		)
		self.assertRepr(
			Const(256, signed(9)).shift_right(15),
			'(s (slice (const 9\'sd-256) 8:9))'
		)

	def test_shift_right_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Shift amount must be an integer, not \'str\'$'
		):
			Const(31).shift_left('str')

	def test_rotate_left(self):
		self.assertRepr(
			Const(256).rotate_left(1),
			'(cat (slice (const 9\'d256) 8:9) (slice (const 9\'d256) 0:8))'
		)
		self.assertRepr(
			Const(256).rotate_left(7),
			'(cat (slice (const 9\'d256) 2:9) (slice (const 9\'d256) 0:2))'
		)
		self.assertRepr(
			Const(256).rotate_left(-1),
			'(cat (slice (const 9\'d256) 1:9) (slice (const 9\'d256) 0:1))'
		)
		self.assertRepr(
			Const(256).rotate_left(-7),
			'(cat (slice (const 9\'d256) 7:9) (slice (const 9\'d256) 0:7))'
		)
		self.assertRepr(
			Const(0, 0).rotate_left(3),
			'(cat (slice (const 0\'d0) 0:0) (slice (const 0\'d0) 0:0))'
		)
		self.assertRepr(
			Const(0, 0).rotate_left(-3),
			'(cat (slice (const 0\'d0) 0:0) (slice (const 0\'d0) 0:0))'
		)

	def test_rotate_left_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Rotate amount must be an integer, not \'str\'$'
		):
			Const(31).rotate_left('str')

	def test_rotate_right(self):
		self.assertRepr(
			Const(256).rotate_right(1),
			'(cat (slice (const 9\'d256) 1:9) (slice (const 9\'d256) 0:1))'
		)
		self.assertRepr(
			Const(256).rotate_right(7),
			'(cat (slice (const 9\'d256) 7:9) (slice (const 9\'d256) 0:7))'
		)
		self.assertRepr(
			Const(256).rotate_right(-1),
			'(cat (slice (const 9\'d256) 8:9) (slice (const 9\'d256) 0:8))'
		)
		self.assertRepr(
			Const(256).rotate_right(-7),
			'(cat (slice (const 9\'d256) 2:9) (slice (const 9\'d256) 0:2))'
		)
		self.assertRepr(
			Const(0, 0).rotate_right(3),
			'(cat (slice (const 0\'d0) 0:0) (slice (const 0\'d0) 0:0))'
		)
		self.assertRepr(
			Const(0, 0).rotate_right(-3),
			'(cat (slice (const 0\'d0) 0:0) (slice (const 0\'d0) 0:0))'
		)

	def test_rotate_right_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Rotate amount must be an integer, not \'str\'$'
		):
			Const(31).rotate_right('str')

	def test_replicate_shape(self):
		s1 = Const(10).replicate(3)
		self.assertEqual(s1.shape(), unsigned(12))
		self.assertIsInstance(s1.shape(), Shape)
		s2 = Const(10).replicate(0)
		self.assertEqual(s2.shape(), unsigned(0))

	def test_replicate_count_wrong(self):
		with self.assertRaises(TypeError):
			Const(10).replicate(-1)
		with self.assertRaises(TypeError):
			Const(10).replicate('str')

	def test_replicate_repr(self):
		s = Const(10).replicate(3)
		self.assertEqual(repr(s), '(cat (const 4\'d10) (const 4\'d10) (const 4\'d10))')

	def test_inc_value(self):
		self.assertRepr(
			Value.cast(1).inc(),
			'(eq (const 1\'d1) (+ (const 1\'d1) (const 1\'d1)))'
		)
		self.assertRepr(
			Value.cast(1).inc(Const(4)),
			'(eq (const 1\'d1) (+ (const 1\'d1) (const 3\'d4)))'
		)

	def test_dec_value(self):
		self.assertRepr(
			Value.cast(1).dec(),
			'(eq (const 1\'d1) (- (const 1\'d1) (const 1\'d1)))'
		)
		self.assertRepr(
			Value.cast(1).dec(Const(4)),
			'(eq (const 1\'d1) (- (const 1\'d1) (const 3\'d4)))'
		)

class ConstTestCase(ToriiTestSuiteCase):
	def test_shape(self):
		self.assertEqual(Const(0).shape(),   unsigned(1))
		self.assertIsInstance(Const(0).shape(), Shape)
		self.assertEqual(Const(1).shape(),   unsigned(1))
		self.assertEqual(Const(10).shape(),  unsigned(4))
		self.assertEqual(Const(-10).shape(), signed(5))

		self.assertEqual(Const(1, 4).shape(),          unsigned(4))
		self.assertEqual(Const(-1, 4).shape(),         signed(4))
		self.assertEqual(Const(1, signed(4)).shape(),  signed(4))
		self.assertEqual(Const(0, unsigned(0)).shape(), unsigned(0))

	def test_shape_wrong(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Width of an unsigned value must be zero or a positive integer, not -1$'
		):
			Const(1, -1)

	def test_wrong_fencepost(self):
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Value 10 equals the non-inclusive end of the constant shape '
			r'range\(0, 10\); this is likely an off-by-one error$'
		):
			Const(10, range(10))

	def test_normalization(self):
		self.assertEqual(Const(0b10110, signed(5)).value, -10)
		self.assertEqual(Const(0b10000, signed(4)).value, 0)
		self.assertEqual(Const(-16, 4).value, 0)

	def test_value(self):
		self.assertEqual(Const(10).value, 10)

	def test_repr(self):
		self.assertEqual(repr(Const(10)),  '(const 4\'d10)')
		self.assertEqual(repr(Const(-10)), '(const 5\'sd-10)')

	def test_hash(self):
		with self.assertRaises(TypeError):
			hash(Const(0))

	def test_shape_castable(self):
		class MockConstValue:
			def __init__(self, value) -> None:
				self.value = value

		class MockConstShape(ShapeCastable):
			def as_shape(self):
				return unsigned(8)

			def __call__(self, value):
				return value

			def const(self, init):
				return MockConstValue(init)

		s = Const(10, MockConstShape())
		self.assertIsInstance(s, MockConstValue)
		self.assertEqual(s.value, 10)

class OperatorTestCase(ToriiTestSuiteCase):
	def test_bool(self):
		v = Const(0, 4).bool()
		self.assertEqual(repr(v), '(b (const 4\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_invert(self):
		v = ~Const(0, 4)
		self.assertEqual(repr(v), '(~ (const 4\'d0))')
		self.assertEqual(v.shape(), unsigned(4))

	def test_as_unsigned(self):
		v = Const(-1, signed(4)).as_unsigned()
		self.assertEqual(repr(v), '(u (const 4\'sd-1))')
		self.assertEqual(v.shape(), unsigned(4))

	def test_as_signed(self):
		v = Const(1, unsigned(4)).as_signed()
		self.assertEqual(repr(v), '(s (const 4\'d1))')
		self.assertEqual(v.shape(), signed(4))

	def test_as_signed_wrong(self):
		with self.assertRaisesRegex(
			ValueError, r'^Cannot create a 0-width signed value$'
		):
			Const(0, 0).as_signed()

	def test_pos(self):
		self.assertRepr(+Const(10), '(const 4\'d10)')

	def test_neg(self):
		v1 = -Const(0, unsigned(4))
		self.assertEqual(repr(v1), '(- (const 4\'d0))')
		self.assertEqual(v1.shape(), signed(5))
		v2 = -Const(0, signed(4))
		self.assertEqual(repr(v2), '(- (const 4\'sd0))')
		self.assertEqual(v2.shape(), signed(5))

	def test_add(self):
		v1 = Const(0, unsigned(4)) + Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(+ (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(7))
		v2 = Const(0, signed(4)) + Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(7))
		v3 = Const(0, signed(4)) + Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(6))
		v4 = Const(0, unsigned(4)) + Const(0, signed(4))
		self.assertEqual(v4.shape(), signed(6))
		v5 = 10 + Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(5))

	def test_sub(self):
		v1 = Const(0, unsigned(4)) - Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(- (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), signed(7))
		v2 = Const(0, signed(4)) - Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(7))
		v3 = Const(0, signed(4)) - Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(6))
		v4 = Const(0, unsigned(4)) - Const(0, signed(4))
		self.assertEqual(v4.shape(), signed(6))
		v5 = 10 - Const(0, 4)
		self.assertEqual(v5.shape(), signed(5))
		v6 = 1 - Const(2)
		self.assertEqual(v6.shape(), signed(3))

	def test_mul(self):
		v1 = Const(0, unsigned(4)) * Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(* (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(10))
		v2 = Const(0, signed(4)) * Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(10))
		v3 = Const(0, signed(4)) * Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(8))
		v5 = 10 * Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(8))

	def test_mod(self):
		v1 = Const(0, unsigned(4)) % Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(% (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(6))
		v3 = Const(0, signed(4)) % Const(0, unsigned(4))
		self.assertEqual(v3.shape(), unsigned(4))
		v4 = Const(0, signed(4)) % Const(0, signed(6))
		self.assertEqual(v4.shape(), signed(6))
		v5 = 10 % Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(4))

	def test_floordiv(self):
		v1 = Const(0, unsigned(4)) // Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(// (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(4))
		v3 = Const(0, signed(4)) // Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(4))
		v4 = Const(0, signed(4)) // Const(0, signed(6))
		self.assertEqual(v4.shape(), signed(5))
		v5 = 10 // Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(4))

	def test_and(self):
		v1 = Const(0, unsigned(4)) & Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(& (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(6))
		v2 = Const(0, signed(4)) & Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(6))
		v3 = Const(0, signed(4)) & Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(5))
		v4 = Const(0, unsigned(4)) & Const(0, signed(4))
		self.assertEqual(v4.shape(), signed(5))
		v5 = 10 & Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(4))

	def test_or(self):
		v1 = Const(0, unsigned(4)) | Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(| (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(6))
		v2 = Const(0, signed(4)) | Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(6))
		v3 = Const(0, signed(4)) | Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(5))
		v4 = Const(0, unsigned(4)) | Const(0, signed(4))
		self.assertEqual(v4.shape(), signed(5))
		v5 = 10 | Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(4))

	def test_xor(self):
		v1 = Const(0, unsigned(4)) ^ Const(0, unsigned(6))
		self.assertEqual(repr(v1), '(^ (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(6))
		v2 = Const(0, signed(4)) ^ Const(0, signed(6))
		self.assertEqual(v2.shape(), signed(6))
		v3 = Const(0, signed(4)) ^ Const(0, unsigned(4))
		self.assertEqual(v3.shape(), signed(5))
		v4 = Const(0, unsigned(4)) ^ Const(0, signed(4))
		self.assertEqual(v4.shape(), signed(5))
		v5 = 10 ^ Const(0, 4)
		self.assertEqual(v5.shape(), unsigned(4))

	def test_shl(self):
		v1 = Const(1, 4) << Const(4)
		self.assertEqual(repr(v1), '(<< (const 4\'d1) (const 3\'d4))')
		self.assertEqual(v1.shape(), unsigned(11))

	def test_shl_wrong(self):
		with self.assertRaisesRegex(TypeError, r'^Shift amount must be unsigned$'):
			1 << Const(0, signed(6))
		with self.assertRaisesRegex(TypeError, r'^Shift amount must be unsigned$'):
			Const(1, unsigned(4)) << -1

	def test_shr(self):
		v1 = Const(1, 4) >> Const(4)
		self.assertEqual(repr(v1), '(>> (const 4\'d1) (const 3\'d4))')
		self.assertEqual(v1.shape(), unsigned(4))

	def test_shr_wrong(self):
		with self.assertRaisesRegex(TypeError, r'^Shift amount must be unsigned$'):
			1 << Const(0, signed(6))
		with self.assertRaisesRegex(TypeError, r'^Shift amount must be unsigned$'):
			Const(1, unsigned(4)) << -1

	def test_lt(self):
		v = Const(0, 4) < Const(0, 6)
		self.assertEqual(repr(v), '(< (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_le(self):
		v = Const(0, 4) <= Const(0, 6)
		self.assertEqual(repr(v), '(<= (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_gt(self):
		v = Const(0, 4) > Const(0, 6)
		self.assertEqual(repr(v), '(> (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_ge(self):
		v = Const(0, 4) >= Const(0, 6)
		self.assertEqual(repr(v), '(>= (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_eq(self):
		v = Const(0, 4) == Const(0, 6)
		self.assertEqual(repr(v), '(== (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_ne(self):
		v = Const(0, 4) != Const(0, 6)
		self.assertEqual(repr(v), '(!= (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v.shape(), unsigned(1))

	def test_mux(self):
		s  = Const(0)
		v1 = Mux(s, Const(0, unsigned(4)), Const(0, unsigned(6)))
		self.assertEqual(repr(v1), '(m (const 1\'d0) (const 4\'d0) (const 6\'d0))')
		self.assertEqual(v1.shape(), unsigned(6))
		v2 = Mux(s, Const(0, signed(4)), Const(0, signed(6)))
		self.assertEqual(v2.shape(), signed(6))
		v3 = Mux(s, Const(0, signed(4)), Const(0, unsigned(4)))
		self.assertEqual(v3.shape(), signed(5))
		v4 = Mux(s, Const(0, unsigned(4)), Const(0, signed(4)))
		self.assertEqual(v4.shape(), signed(5))

	def test_mux_wide(self):
		s = Const(0b100)
		v = Mux(s, Const(0, unsigned(4)), Const(0, unsigned(6)))
		self.assertEqual(repr(v), '(m (const 3\'d4) (const 4\'d0) (const 6\'d0))')

	def test_mux_bool(self):
		v = Mux(True, Const(0), Const(0))
		self.assertEqual(repr(v), '(m (const 1\'d1) (const 1\'d0) (const 1\'d0))')

	def test_any(self):
		v = Const(0b101).any()
		self.assertEqual(repr(v), '(r| (const 3\'d5))')

	def test_all(self):
		v = Const(0b101).all()
		self.assertEqual(repr(v), '(r& (const 3\'d5))')

	def test_xor_value(self):
		v = Const(0b101).xor()
		self.assertEqual(repr(v), '(r^ (const 3\'d5))')

	def test_matches(self):
		s = Signal(4)
		with self.assertWarns(
			SyntaxWarning,
			msg = 'Value.matches() with an empty patterns clause will return `Const(0)` in a future release.'
		):
			self.assertRepr(s.matches(), '(const 1\'d1)')
		self.assertRepr(s.matches(1), '''
		(== (sig s) (const 1'd1))
		''')
		self.assertRepr(s.matches(0, 1), '''
		(r| (cat (== (sig s) (const 1'd0)) (== (sig s) (const 1'd1))))
		''')
		self.assertRepr(s.matches('10--'), '''
		(== (& (sig s) (const 4'd12)) (const 4'd8))
		''')
		self.assertRepr(s.matches('1 0--'), '''
		(== (& (sig s) (const 4'd12)) (const 4'd8))
		''')

	def test_matches_enum(self):
		s = Signal(SignedEnum)
		self.assertRepr(s.matches(SignedEnum.FOO), '''
		(== (sig s) (const 2'sd-1))
		''')

	def test_matches_const_castable(self):
		s = Signal(4)
		self.assertRepr(s.matches(Cat(Const(0b10, 2), Const(0b11, 2))), '''
		(== (sig s) (const 4'd14))
		''')

	def test_matches_width_wrong(self):
		s = Signal(4)
		with self.assertRaisesRegex(
			SyntaxError,
			r'^Match pattern \'--\' must have the same width as match value \(which is 4\)$'
		):
			s.matches('--')
		with self.assertWarnsRegex(
			SyntaxWarning, (
				r'^Match pattern \'22\' \(5\'10110\) is wider than match value \(which has width 4\); '
				r'comparison will never be true$'
			)
		):
			s.matches(0b10110)

		with self.assertWarns(
			SyntaxWarning,
			msg = 'Match pattern \'(cat (const 1\'d0) (const 4\'d11))\' (5\'10110) is wider than match value (which has width 4); comparison will never be true' # noqa: E501
		):
			s.matches(Cat(0, Const(0b1011, 4)))

	def test_matches_bits_wrong(self):
		s = Signal(4)
		with self.assertRaisesRegex(
			SyntaxError, (
				r'^Match pattern \'abc\' must consist of 0, 1, and - \(don\'t care\) bits, '
				r'and may include whitespace$'
			)
		):
			s.matches('abc')

	def test_matches_pattern_wrong(self):
		s = Signal(4)
		with self.assertRaisesRegex(
			SyntaxError,
			r'^Match pattern must be a string or a const-castable expression, not 1\.0$'
		):
			s.matches(1.0)

	def test_hash(self):
		with self.assertRaises(TypeError):
			hash(Const(0) + Const(0))

	def test_abs(self):
		s = Signal(4)
		self.assertRepr(abs(s), '(sig s)')
		s = Signal(signed(4))
		self.assertRepr(
			abs(s),
			'(slice (m (>= (sig s) (const 1\'d0)) (sig s) (- (sig s))) 0:4)'
		)
		self.assertEqual(abs(s).shape(), unsigned(4))

	def test_contains(self):
		with self.assertRaises(TypeError, msg = 'The python `in` operator is not supported on Torii values'):
			1 in Signal(3)

class SliceTestCase(ToriiTestSuiteCase):
	def test_shape(self):
		s1 = Const(10)[2]
		self.assertEqual(s1.shape(), unsigned(1))
		self.assertIsInstance(s1.shape(), Shape)
		s2 = Const(-10)[0:2]
		self.assertEqual(s2.shape(), unsigned(2))

	def test_start_end_negative(self):
		c  = Const(0, 8)
		s1 = Slice(c, 0, -1)
		self.assertEqual((s1.start, s1.stop), (0, 7))
		s1 = Slice(c, -4, -1)
		self.assertEqual((s1.start, s1.stop), (4, 7))

	def test_start_end_bool(self):
		c  = Const(0, 8)
		s  = Slice(c, False, True)
		self.assertIs(type(s.start), int)
		self.assertIs(type(s.stop),  int)

	def test_start_end_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Slice start must be an integer, not \'x\'$'
		):
			Slice(0, 'x', 1)
		with self.assertRaisesRegex(
			TypeError,
			r'^Slice stop must be an integer, not \'x\'$'
		):
			Slice(0, 1, 'x')

	def test_start_end_out_of_range(self):
		c = Const(0, 8)
		with self.assertRaisesRegex(
			IndexError,
			r'^Cannot start slice 10 bits into 8-bit value$'
		):
			Slice(c, 10, 12)
		with self.assertRaisesRegex(
			IndexError,
			r'^Cannot stop slice 12 bits into 8-bit value$'
		):
			Slice(c, 0, 12)
		with self.assertRaisesRegex(
			IndexError,
			r'^Slice start 4 must be less than slice stop 2$'
		):
			Slice(c, 4, 2)
		with self.assertRaisesRegex(
			IndexError,
			r'^Cannot start slice -9 bits into 8-bit value$'
		):
			Slice(c, -9, -5)
		with self.assertRaisesRegex(
			IndexError,
			r'^Cannot stop slice 9 bits into 8-bit value$'
		):
			Slice(c, 5, 9)

	def test_repr(self):
		s1 = Const(10)[2]
		self.assertEqual(repr(s1), '(slice (const 4\'d10) 2:3)')

	def test_const(self):
		a = Const.cast(Const(0x1234, 16)[4:12])
		self.assertEqual(a.value, 0x23)
		self.assertEqual(a.width, 8)
		self.assertEqual(a.signed, False)
		a = Const.cast(Const(-4, signed(8))[1:6])
		self.assertEqual(a.value, 0x1e)
		self.assertEqual(a.width, 5)
		self.assertEqual(a.signed, False)

class BitSelectTestCase(ToriiTestSuiteCase):
	def setUp(self):
		self.c = Const(0, 8)
		self.s = Signal(range(self.c.width))

	def test_shape(self):
		s1 = self.c.bit_select(self.s, 2)
		self.assertIsInstance(s1, Part)
		self.assertEqual(s1.shape(), unsigned(2))
		self.assertIsInstance(s1.shape(), Shape)
		s2 = self.c.bit_select(self.s, 0)
		self.assertIsInstance(s2, Part)
		self.assertEqual(s2.shape(), unsigned(0))

	def test_stride(self):
		s1 = self.c.bit_select(self.s, 2)
		self.assertIsInstance(s1, Part)
		self.assertEqual(s1.stride, 1)

	def test_const(self):
		s1 = self.c.bit_select(1, 2)
		self.assertIsInstance(s1, Slice)
		self.assertRepr(s1, '(slice (const 8\'d0) 1:3)')

	def test_width_wrong(self):
		with self.assertRaises(TypeError):
			self.c.bit_select(self.s, -1)

	def test_repr(self):
		s = self.c.bit_select(self.s, 2)
		self.assertEqual(repr(s), '(part (const 8\'d0) (sig s) 2 1)')

	def test_offset_wrong(self):
		with self.assertRaisesRegex(TypeError, r'^Part offset must be unsigned$'):
			self.c.bit_select(self.s.as_signed(), 1)

class WordSelectTestCase(ToriiTestSuiteCase):
	def setUp(self):
		self.c = Const(0, 8)
		self.s = Signal(range(self.c.width))

	def test_shape(self):
		s1 = self.c.word_select(self.s, 2)
		self.assertIsInstance(s1, Part)
		self.assertEqual(s1.shape(), unsigned(2))
		self.assertIsInstance(s1.shape(), Shape)

	def test_stride(self):
		s1 = self.c.word_select(self.s, 2)
		self.assertIsInstance(s1, Part)
		self.assertEqual(s1.stride, 2)

	def test_const(self):
		s1 = self.c.word_select(1, 2)
		self.assertIsInstance(s1, Slice)
		self.assertRepr(s1, '(slice (const 8\'d0) 2:4)')

	def test_width_wrong(self):
		with self.assertRaises(TypeError):
			self.c.word_select(self.s, 0)
		with self.assertRaises(TypeError):
			self.c.word_select(self.s, -1)

	def test_repr(self):
		s = self.c.word_select(self.s, 2)
		self.assertEqual(repr(s), '(part (const 8\'d0) (sig s) 2 2)')

	def test_offset_wrong(self):
		with self.assertRaisesRegex(TypeError, r'^Part offset must be unsigned$'):
			self.c.word_select(self.s.as_signed(), 1)

class CatTestCase(ToriiTestSuiteCase):
	def test_shape(self):
		c0 = Cat()
		self.assertEqual(c0.shape(), unsigned(0))
		self.assertIsInstance(c0.shape(), Shape)
		c1 = Cat(Const(10))
		self.assertEqual(c1.shape(), unsigned(4))
		c2 = Cat(Const(10), Const(1))
		self.assertEqual(c2.shape(), unsigned(5))
		c3 = Cat(Const(10), Const(1), Const(0))
		self.assertEqual(c3.shape(), unsigned(6))

	def test_repr(self):
		c1 = Cat(Const(10), Const(1))
		self.assertEqual(repr(c1), '(cat (const 4\'d10) (const 1\'d1))')

	def test_cast(self):
		c = Cat(1, 0)
		self.assertEqual(repr(c), '(cat (const 1\'d1) (const 1\'d0))')

	def test_str_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Object \'foo\' cannot be converted to a Torii value$'
		):
			Cat('foo')

	def test_int_01(self):
		with warnings.catch_warnings():
			warnings.filterwarnings(action = 'error', category = SyntaxWarning)
			Cat(0, 1, 1, 0)

	def test_enum_wrong(self):
		class Color(Enum):
			RED  = 1
			BLUE = 2

		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Argument #1 of \'Cat\(\)\' is an enumerated value <Color\.RED: 1> without '
			r'a defined shape used in a bit vector context; use \'Const\' to specify '
			r'the shape\.$',
		):
			c = Cat(Color.RED, Color.BLUE)
		self.assertEqual(repr(c), '(cat (const 2\'d1) (const 2\'d2))')

	def test_intenum_wrong(self):
		class Color(int, Enum):
			RED  = 1
			BLUE = 2

		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Argument #1 of \'Cat\(\)\' is an enumerated value <Color\.RED: 1> '
			r'without a defined shape used in a bit vector context; use \'Const\' to specify '
			r'the shape\.$'

		):
			c = Cat(Color.RED, Color.BLUE)
		self.assertEqual(repr(c), '(cat (const 2\'d1) (const 2\'d2))')

	def test_int_wrong(self):
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Argument #1 of \'Cat\(\)\' is a bare integer 2 used in bit vector context; '
			r'consider specifying the width explicitly using \'Const\(2, 2\)\' instead$'
		):
			Cat(2)

	def test_const(self):
		a = Const.cast(Cat(Const(1, 1), Const(0, 1), Const(3, 2), Const(2, 2)))
		self.assertEqual(a.value, 0x2d)
		self.assertEqual(a.width, 6)
		self.assertEqual(a.signed, False)
		a = Const.cast(Cat(Const(-4, 8), Const(-3, 8)))
		self.assertEqual(a.value, 0xfdfc)
		self.assertEqual(a.width, 16)
		self.assertEqual(a.signed, False)

class ArrayTestCase(ToriiTestSuiteCase):
	def test_acts_like_array(self):
		a = Array([1, 2, 3])
		self.assertSequenceEqual(a, [1, 2, 3])
		self.assertEqual(a[1], 2)
		a[1] = 4
		self.assertSequenceEqual(a, [1, 4, 3])
		del a[1]
		self.assertSequenceEqual(a, [1, 3])
		a.insert(1, 2)
		self.assertSequenceEqual(a, [1, 2, 3])

	def test_becomes_immutable(self):
		a = Array([1, 2, 3])
		s1 = Signal(range(len(a)))
		s2 = Signal(range(len(a)))
		a[s1]
		a[s2]
		with self.assertRaisesRegex(
			ValueError,
			r'^Array can no longer be mutated after it was indexed with a value at '
		):
			a[1] = 2
		with self.assertRaisesRegex(
			ValueError,
			r'^Array can no longer be mutated after it was indexed with a value at '
		):
			del a[1]
		with self.assertRaisesRegex(
			ValueError,
			r'^Array can no longer be mutated after it was indexed with a value at '
		):
			a.insert(1, 2)

	def test_index_value_castable(self):
		class MyValue(ValueCastable):
			@ValueCastable.lowermethod
			def as_value(self):
				return Signal()

			def shape():
				return unsigned(1)

		a = Array([1, 2, 3])
		a[MyValue()]

	def test_repr(self):
		a = Array([1, 2, 3])
		self.assertEqual(repr(a), '(array mutable [1, 2, 3])')
		s = Signal(range(len(a)))
		a[s]
		self.assertEqual(repr(a), '(array [1, 2, 3])')

class ArrayProxyTestCase(ToriiTestSuiteCase):
	def test_index_shape(self):
		m = Array(Array(x * y for y in range(1, 4)) for x in range(1, 4))
		a = Signal(range(3))
		b = Signal(range(3))
		v = m[a][b]
		self.assertEqual(v.shape(), unsigned(4))

	def test_attr_shape(self):
		from collections import namedtuple
		pair = namedtuple('pair', ('p', 'n'))
		a = Array(pair(i, -i) for i in range(10))
		s = Signal(range(len(a)))
		v = a[s]
		self.assertEqual(v.p.shape(), unsigned(4))
		self.assertEqual(v.n.shape(), signed(5))

	def test_attr_shape_signed(self):
		# [unsigned(1), unsigned(1)] → unsigned(1)
		a1 = Array([1, 1])
		v1 = a1[Const(0)]
		self.assertEqual(v1.shape(), unsigned(1))
		# [signed(1), signed(1)] → signed(1)
		a2 = Array([-1, -1])
		v2 = a2[Const(0)]
		self.assertEqual(v2.shape(), signed(1))
		# [unsigned(1), signed(2)] → signed(2)
		a3 = Array([1, -2])
		v3 = a3[Const(0)]
		self.assertEqual(v3.shape(), signed(2))
		# [unsigned(1), signed(1)] → signed(2); 1st operand padded with sign bit!
		a4 = Array([1, -1])
		v4 = a4[Const(0)]
		self.assertEqual(v4.shape(), signed(2))
		# [unsigned(2), signed(1)] → signed(3); 1st operand padded with sign bit!
		a5 = Array([1, -1])
		v5 = a5[Const(0)]
		self.assertEqual(v5.shape(), signed(2))

	def test_repr(self):
		a = Array([1, 2, 3])
		s = Signal(range(3))
		v = a[s]
		self.assertEqual(repr(v), '(proxy (array [1, 2, 3]) (sig s))')

class SignalTestCase(ToriiTestSuiteCase):
	def test_shape(self):
		s1 = Signal()
		self.assertEqual(s1.shape(), unsigned(1))
		self.assertIsInstance(s1.shape(), Shape)
		s2 = Signal(2)
		self.assertEqual(s2.shape(), unsigned(2))
		s3 = Signal(unsigned(2))
		self.assertEqual(s3.shape(), unsigned(2))
		s4 = Signal(signed(2))
		self.assertEqual(s4.shape(), signed(2))
		s5 = Signal(0)
		self.assertEqual(s5.shape(), unsigned(0))
		s6 = Signal(range(16))
		self.assertEqual(s6.shape(), unsigned(4))
		s7 = Signal(range(4, 16))
		self.assertEqual(s7.shape(), unsigned(4))
		s8 = Signal(range(-4, 16))
		self.assertEqual(s8.shape(), signed(5))
		s9 = Signal(range(-20, 16))
		self.assertEqual(s9.shape(), signed(6))
		s10 = Signal(range(0))
		self.assertEqual(s10.shape(), unsigned(0))
		s11 = Signal(range(1))
		self.assertEqual(s11.shape(), unsigned(0))

	def test_shape_wrong(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Width of an unsigned value must be zero or a positive integer, not -10$'
		):
			Signal(-10)

	def test_name(self):
		s1 = Signal()
		self.assertEqual(s1.name, 's1')
		s2 = Signal(name = 'sig')
		self.assertEqual(s2.name, 'sig')

	def test_reset(self):
		s1 = Signal(4, reset = 0b111, reset_less = True)
		self.assertEqual(s1.reset, 0b111)
		self.assertEqual(s1.reset_less, True)

	def test_reset_enum(self):
		s1 = Signal(2, reset = UnsignedEnum.BAR)
		self.assertEqual(s1.reset, 2)
		with self.assertRaisesRegex(
			TypeError,
			r'^Reset value must be a constant-castable expression, '
			r'not <StringEnum\.FOO: \'a\'>$'
		):
			Signal(1, reset = StringEnum.FOO)

	def test_reset_shape_castable_const(self):
		class CastableFromHex(ShapeCastable):
			def as_shape(self):
				return unsigned(8)

			def const(self, init):
				return int(init, 16)

		s1 = Signal(CastableFromHex(), reset = 'aa')
		self.assertEqual(s1.reset, 0xaa)

		with self.assertRaisesRegex(
			ValueError,
			r'^Constant returned by <.+?CastableFromHex.+?>\.const\(\) must have the shape '
			r'that it casts to, unsigned\(8\), and not unsigned\(1\)$'
		):
			Signal(CastableFromHex(), reset="01")

	def test_reset_signed_mismatch(self):
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Reset value -2 is signed, but the signal shape is unsigned\(2\)$'
		):
			Signal(unsigned(2), reset = -2)

	def test_reset_wrong_too_wide(self):
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^^Reset value 2 will be truncated to the signal shape unsigned\(1\)$'
		):
			Signal(unsigned(1), reset = 2)
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Reset value 1 will be truncated to the signal shape signed\(1\)$'
		):
			Signal(signed(1), reset = 1)
		with self.assertWarnsRegex(
			SyntaxWarning,
			r'^Reset value -2 will be truncated to the signal shape signed\(1\)$'
		):
			Signal(signed(1), reset = -2)

	def test_reset_wrong_fencepost(self):
		with self.assertRaisesRegex(
			SyntaxError,
			r'^Reset value 10 equals the non-inclusive end of the signal shape '
			r'range\(0, 10\); this is likely an off-by-one error$'
		):
			Signal(range(0, 10), reset = 10)

		with self.assertRaisesRegex(
			SyntaxError,
			r'^Reset value 0 equals the non-inclusive end of the signal shape '
			r'range\(0, 0\); this is likely an off-by-one error$'
		):
			Signal(range(0), reset = 0)

	def test_reset_wrong_range(self):
		with self.assertRaisesRegex(
			SyntaxError,
			r'^Reset value 11 is not within the signal shape range\(0, 10\)$'
		):
			Signal(range(0, 10), reset = 11)

		with self.assertRaisesRegex(
			SyntaxError,
			r'^Reset value 0 is not within the signal shape range\(1, 10\)$'
		):
			Signal(range(1, 10), reset = 0)

	def test_attrs(self):
		s1 = Signal()
		self.assertEqual(s1.attrs, {})
		s2 = Signal(attrs = {'no_retiming': True})
		self.assertEqual(s2.attrs, {'no_retiming': True})

	def test_repr(self):
		s1 = Signal()
		self.assertEqual(repr(s1), '(sig s1)')

	def test_like(self):
		s1 = Signal.like(Signal(4))
		self.assertEqual(s1.shape(), unsigned(4))
		s2 = Signal.like(Signal(range(-15, 1)))
		self.assertEqual(s2.shape(), signed(5))
		s3 = Signal.like(Signal(4, reset = 0b111, reset_less = True))
		self.assertEqual(s3.reset, 0b111)
		self.assertEqual(s3.reset_less, True)
		s4 = Signal.like(Signal(attrs = {'no_retiming': True}))
		self.assertEqual(s4.attrs, {'no_retiming': True})
		s5 = Signal.like(Signal(decoder = str))
		self.assertEqual(s5.decoder, str)
		s6 = Signal.like(10)
		self.assertEqual(s6.shape(), unsigned(4))
		s7 = [Signal.like(Signal(4))][0]
		self.assertEqual(s7.name, '$like')
		s8 = Signal.like(s1, name_suffix = '_ff')
		self.assertEqual(s8.name, 's1_ff')

	def test_decoder(self):
		class Color(Enum):
			RED  = 1
			BLUE = 2
		s = Signal(decoder = Color)
		self.assertEqual(s.decoder(1), 'RED/1')
		self.assertEqual(s.decoder(3), '3')

	def test_enum(self):
		s1 = Signal(UnsignedEnum)
		self.assertEqual(s1.shape(), unsigned(2))
		s2 = Signal(SignedEnum)
		self.assertEqual(s2.shape(), signed(2))
		self.assertEqual(s2.decoder(SignedEnum.FOO), 'FOO/-1')

	def test_const_wrong(self):
		s1 = Signal()
		with self.assertRaises(TypeError, msg = 'Value (sig s1) cannot be converted to a Torii constant'):
			Const.cast(s1)

class ClockSignalTestCase(ToriiTestSuiteCase):
	def test_domain(self):
		s1 = ClockSignal()
		self.assertEqual(s1.domain, 'sync')
		s2 = ClockSignal('pix')
		self.assertEqual(s2.domain, 'pix')

		with self.assertRaisesRegex(
			TypeError,
			r'^Clock domain name must be a string, not 1$'
		):
			ClockSignal(1)

	def test_shape(self):
		s1 = ClockSignal()
		self.assertEqual(s1.shape(), unsigned(1))
		self.assertIsInstance(s1.shape(), Shape)

	def test_repr(self):
		s1 = ClockSignal()
		self.assertEqual(repr(s1), '(clk sync)')

	def test_wrong_name_comb(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Domain \'comb\' does not have a clock$'
		):
			ClockSignal('comb')

class ResetSignalTestCase(ToriiTestSuiteCase):
	def test_domain(self):
		s1 = ResetSignal()
		self.assertEqual(s1.domain, 'sync')
		s2 = ResetSignal('pix')
		self.assertEqual(s2.domain, 'pix')

		with self.assertRaisesRegex(
			TypeError,
			r'^Clock domain name must be a string, not 1$'
		):
			ResetSignal(1)

	def test_shape(self):
		s1 = ResetSignal()
		self.assertEqual(s1.shape(), unsigned(1))
		self.assertIsInstance(s1.shape(), Shape)

	def test_repr(self):
		s1 = ResetSignal()
		self.assertEqual(repr(s1), '(rst sync)')

	def test_wrong_name_comb(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Domain \'comb\' does not have a reset$'
		):
			ResetSignal('comb')

class MockValueCastable(ValueCastable):
	def __init__(self, dest) -> None:
		self.dest = dest

	def shape(self):
		return Value.cast(self.dest).shape()

	@ValueCastable.lowermethod
	def as_value(self):
		return self.dest

class MockValueCastableChanges(ValueCastable):
	def __init__(self, width = 0) -> None:
		self.width = width

	def shape(self):
		return unsigned(self.width)

	@ValueCastable.lowermethod
	def as_value(self):
		return Signal(self.width)

class MockValueCastableCustomGetattr(ValueCastable):
	def __init__(self) -> None:
		pass

	def shape(self):
		raise AssertionError(False)

	@ValueCastable.lowermethod
	def as_value(self):
		return Const(0)

	def __getattr__(self, attr):
		assert False

class ValueCastableTestCase(ToriiTestSuiteCase):
	def test_not_decorated(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Class \'MockValueCastableNotDecorated\' deriving from `ValueCastable` must '
			r'decorate the `as_value` method with the `ValueCastable.lowermethod` decorator$'
		):
			class MockValueCastableNotDecorated(ValueCastable):
				def __init__(self) -> None:
					pass # :nocov:

				def shape(self):
					pass # :nocov:

				def as_value(self):
					return Signal() # :nocov:

	def test_no_override(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Class \'MockValueCastableNoOverrideAsValue\' deriving from `ValueCastable` must '
			r'override the `as_value` method$'
		):
			class MockValueCastableNoOverrideAsValue(ValueCastable):
				def __init__(self) -> None:
					pass # :nocov:

		with self.assertRaisesRegex(
			TypeError,
			r'^Class \'MockValueCastableNoOverrideShape\' deriving from `ValueCastable` must '
			r'override the `shape` method$'
		):
			class MockValueCastableNoOverrideShape(ValueCastable):
				def __init__(self) -> None:
					pass # :nocov:

				def as_value(self):
					return Signal() # :nocov:

	def test_memoized(self):
		vc = MockValueCastableChanges(1)
		sig1 = vc.as_value()
		vc.width = 2
		sig2 = vc.as_value()
		self.assertIs(sig1, sig2)
		vc.width = 3
		sig3 = Value.cast(vc)
		self.assertIs(sig1, sig3)

	def test_custom_getattr(self):
		vc = MockValueCastableCustomGetattr()
		vc.as_value() # shouldn't call __getattr__

	def test_recurse_bad(self):
		vc = MockValueCastable(None)
		vc.dest = vc
		with self.assertRaisesRegex(
			RecursionError,
			r'^Value-castable object <.+> casts to itself$'
		):
			Value.cast(vc)

	def test_recurse(self):
		vc = MockValueCastable(MockValueCastable(Signal()))
		self.assertIsInstance(Value.cast(vc), Signal)

class ValueLikeTestCase(ToriiTestSuiteCase):
	def test_construct(self):
		with self.assertRaises(TypeError):
			ValueLike()

	def test_subclass(self):
		self.assertTrue(issubclass(Value, ValueLike))
		self.assertTrue(issubclass(MockValueCastable, ValueLike))
		self.assertTrue(issubclass(int, ValueLike))
		self.assertFalse(issubclass(range, ValueLike))
		self.assertFalse(issubclass(EnumMeta, ValueLike))
		self.assertTrue(issubclass(Enum, ValueLike))
		self.assertFalse(issubclass(str, ValueLike))
		self.assertTrue(issubclass(ValueLike, ValueLike))

	def test_isinstance(self):
		self.assertTrue(isinstance(Const(0, 2), ValueLike))
		self.assertTrue(isinstance(MockValueCastable(Const(0, 2)), ValueLike))
		self.assertTrue(isinstance(2, ValueLike))
		self.assertTrue(isinstance(-2, ValueLike))
		self.assertFalse(isinstance(range(10), ValueLike))

	def test_enum(self):
		class EnumA(Enum):
			A = 1
			B = 2

		class EnumB(Enum):
			A = 'a'
			B = 'b'

		class EnumC(Enum):
			A = Cat(Const(1, 2), Const(0, 2))

		class EnumD(Enum):
			A = 1
			B = 'a'

		self.assertTrue(issubclass(EnumA, ValueLike))
		self.assertFalse(issubclass(EnumB, ValueLike))
		self.assertTrue(issubclass(EnumC, ValueLike))
		self.assertFalse(issubclass(EnumD, ValueLike))
		self.assertTrue(isinstance(EnumA.A, ValueLike))
		self.assertFalse(isinstance(EnumB.A, ValueLike))
		self.assertTrue(isinstance(EnumC.A, ValueLike))
		self.assertFalse(isinstance(EnumD.A, ValueLike))

class SampleDUT(Elaboratable):
	def __init__(self, v: Signal, s: Signal, clocks: int, mode: str | None = None) -> None:
		self.v = v
		self.s = s

		self.clocks = clocks
		self.mode   = mode

	def elaborate(self, platform) -> Module:
		m = Module()

		m.domains += ClockDomain('sync')

		match self.mode:
			case 'edge':
				m.d.sync += [ self.s.eq(Edge(self.v, self.clocks)), ]
			case 'rose':
				m.d.sync += [ self.s.eq(Rose(self.v, self.clocks)), ]
			case 'fell':
				m.d.sync += [ self.s.eq(Fell(self.v, self.clocks)), ]
			case 'past':
				m.d.sync += [ self.s.eq(Past(self.v, self.clocks)), ]
			case 'stable':
				m.d.sync += [ self.s.eq(Stable(self.v, self.clocks)), ]
			case _:
				m.d.sync += [ self.s.eq(Sample(self.v, self.clocks, None)), ]
		return m

class SampleTestCase(ToriiTestSuiteCase):
	def test_const(self):
		s = Sample(1, 1, 'sync')
		self.assertEqual(s.shape(), unsigned(1))

	def test_signal(self):
		s1 = Sample(Signal(2), 1, 'sync')
		self.assertEqual(s1.shape(), unsigned(2))

		Sample(ClockSignal(), 1, 'sync')
		Sample(ResetSignal(), 1, 'sync')

	def test_wrong_value_operator(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Sampled value must be a signal or a constant, not '
				r'\(\+ \(sig \$signal\) \(const 1\'d1\)\)$'
			)
		):
			Sample(Signal() + 1, 1, 'sync')

	def test_wrong_clocks_neg(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Cannot sample a value 1 cycles in the future$'
		):
			Sample(Signal(), -1, 'sync')

	def test_wrong_domain(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Domain name must be a string or None, not 0$'
		):
			Sample(Signal(), 1, 0)

	def test_sample_delay0(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 0))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_delay1(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 1))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_edge(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 0, 'edge'))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_fell(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 0, 'fell'))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_past(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 1, 'past'))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_rose(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 0, 'rose'))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

	def test_sample_stable(self):
		v = Signal()
		s = Signal()

		sim = Simulator(SampleDUT(v, s, 0, 'stable'))
		sim.add_clock(1e-6)

		def proc():
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield v.eq(0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield v.eq(1)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 1)
			self.assertEqual((yield s), 0)
			yield v.eq(0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 0)
			yield Tick()
			yield Delay(1e-8)
			self.assertEqual((yield v), 0)
			self.assertEqual((yield s), 1)
			yield Tick()
			yield Delay(1e-8)

		sim.add_process(proc)
		with sim.write_vcd('test.vcd'):
			sim.run()

class InitialTestCase(ToriiTestSuiteCase):
	def test_initial(self):
		i = Initial()
		self.assertEqual(i.shape(), unsigned(1))

class SwitchTestCase(ToriiTestSuiteCase):
	def test_default_case(self):
		s = Switch(Const(0), {None: []})
		self.assertEqual(s.cases, {(): []})

	def test_int_case(self):
		s = Switch(Const(0, 8), {10: []})
		self.assertEqual(s.cases, {('00001010',): []})

	def test_int_neg_case(self):
		s = Switch(Const(0, 8), {-10: []})
		self.assertEqual(s.cases, {('11110110',): []})

	def test_int_zero_width(self):
		s = Switch(Const(0, 0), {0: []})
		self.assertEqual(s.cases, {('',): []})

	def test_int_zero_width_enum(self):
		class ZeroEnum(Enum):
			A = 0

		s = Switch(Const(0, 0), {ZeroEnum.A: []})
		self.assertEqual(s.cases, {('',): []})

	def test_enum_case(self):
		s = Switch(Const(0, UnsignedEnum), {UnsignedEnum.FOO: []})
		self.assertEqual(s.cases, {('01',): []})

	def test_str_case(self):
		s = Switch(Const(0, 8), {'0000 11\t01': []})
		self.assertEqual(s.cases, {('00001101',): []})

	def test_two_cases(self):
		s = Switch(Const(0, 8), {('00001111', 123): []})
		self.assertEqual(s.cases, {('00001111', '01111011'): []})
