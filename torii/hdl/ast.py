# SPDX-License-Identifier: BSD-2-Clause

import functools
import warnings
import operator

from abc               import ABCMeta, abstractmethod
from collections       import OrderedDict
from collections.abc   import (
	Iterable, Iterator, Mapping, MutableMapping, MutableSequence, MutableSet, Sequence, Callable, Generator
)
from typing            import (
	TYPE_CHECKING, TypeAlias, TypeVar, Literal, NoReturn, Generic, ParamSpec, SupportsIndex
)
from types             import NotImplementedType
from enum              import Enum, EnumMeta
from itertools         import chain

# For Python <= 3.10
from typing_extensions import TypeVarTuple, Unpack

from ..util            import flatten, tracer, union
from ..util.decorators import final
from ..util.units      import bits_for
from ._unused          import MustUse, UnusedMustUse
from .._typing         import SrcLoc, SwitchCaseT

__all__ = (
	'AnyConst',
	'AnySeq',
	'Array',
	'ArrayProxy',
	'Assert',
	'Assign',
	'Assume',
	'Cat',
	'ClockSignal',
	'Const',
	'Cover',
	'Fell',
	'Initial',
	'Mux',
	'Operator',
	'Part',
	'Past',
	'Property',
	'ResetSignal',
	'Rose',
	'Sample',
	'Shape',
	'ShapeCastable',
	'ShapeLike',
	'Signal',
	'SignalDict',
	'SignalKey',
	'SignalSet',
	'signed',
	'Slice',
	'Stable',
	'Statement',
	'Switch',
	'unsigned',
	'Value',
	'ValueCastable',
	'ValueLike',
	'ValueDict',
	'ValueKey',
	'ValueSet',
)

T = TypeVar('T')
U = TypeVar('U')

Params     = ParamSpec('Params')
ReturnType = TypeVar('ReturnType')

ShapeCastT: TypeAlias = 'Shape | int | bool | range | type | ShapeCastable'
ValueCastT: TypeAlias = 'Value | int | bool | EnumMeta | ValueCastable | ValueLike'


class DUID:
	''' Deterministic Unique IDentifier. '''
	__next_uid = 0

	def __init__(self) -> None:
		self.duid = DUID.__next_uid
		DUID.__next_uid += 1

class ShapeCastable(metaclass = ABCMeta):
	'''
	Interface of user-defined objects that can be cast to :class:`Shape`s.

	An object deriving from :class:`ShapeCastable` is automatically converted to a :class:`Shape`
	when it is used in a context where a :class:`Shape` is expected. Such objects can contain
	a richer description of the shape than what is supported by the core Torii language, yet
	still be transparently used with it.

	'''

	@abstractmethod
	def as_shape(self) -> 'Shape':
		raise TypeError(f'Class \'{type(self).__name__}\' deriving from `ShapeCastable` must override the `as_shape` method')

	@abstractmethod
	def const(self, val: 'ValueCastT | None') -> 'Const':
		raise TypeError(f'Class \'{type(self).__name__}\' deriving from `ShapeCastable` must override the `const` method')

class Shape:
	'''
	Bit width and signedness of a value.

	A ``Shape`` can be constructed using:

	  * explicit bit width and signedness;
	  * aliases :func:`signed` and :func:`unsigned`;
	  * casting from a variety of objects.

	A ``Shape`` can be cast from:

	  * an integer, where the integer specifies the bit width;
	  * a range, where the result is wide enough to represent any element of the range, and is
		signed if any element of the range is signed;
	  * an :class:`Enum` with all integer members or :class:`IntEnum`, where the result is wide
		enough to represent any member of the enumeration, and is signed if any member of
		the enumeration is signed.

	Parameters
	----------
	width : int
		The number of bits in the representation, including the sign bit (if any).
	signed : bool
		If ``False``, the value is unsigned. If ``True``, the value is signed two's complement.

	'''  # noqa: E101

	def __init__(self, width: int = 1, signed: bool = False) -> None:
		if not isinstance(width, int):
			raise TypeError(f'Width must be an integer, not {width!r}')
		if not signed and width < 0:
			raise ValueError(f'Width of an unsigned value must be zero or a positive integer, not {width}')
		if signed and width <= 0:
			raise ValueError(f'Width of a signed value must be a positive integer, not {width}')

		self.width = width
		self.signed = signed

	# This implements an algorithm for inferring shape from standard Python enumerations
	# for `Shape.cast()`.
	@staticmethod
	def _cast_plain_enum(obj: EnumMeta) -> 'Shape':
		signed = False
		width  = 0
		# TODO(aki): This needs proper typing, rather than just being ignored, however I'm not sure that
		#         	 it's possible as EnumMeta is not generically typed therefore we can't really ensure
		#            that the `.value` is a `ValueCastType`
		for member in obj: # type: ignore
			try:
				member_shape = Const.cast(member.value).shape() # type: ignore
			except TypeError:
				raise TypeError(
					'Only enumerations whose members have constant-castable '
					'values can be used in Torii code'
				)
			if not signed and member_shape.signed:
				signed = True
				width  = max(width + 1, member_shape.width)
			elif signed and not member_shape.signed:
				width  = max(width, member_shape.width + 1)
			else:
				width  = max(width, member_shape.width)
		return Shape(width, signed)

	@staticmethod
	def cast(obj: object, *, src_loc_at: int = 0) -> 'Shape':
		while True:
			if isinstance(obj, Shape):
				return obj
			elif isinstance(obj, ShapeCastable):
				new_obj = obj.as_shape()
			elif isinstance(obj, int):
				return Shape(obj)
			elif isinstance(obj, range):
				if len(obj) == 0:
					return Shape(0)
				signed = obj[0] < 0 or obj[-1] < 0
				width  = max(
					bits_for(obj[0], signed),
					bits_for(obj[-1], signed)
				)
				if obj[0] == obj[-1] == 0:
					width = 0
				return Shape(width, signed)
			elif isinstance(obj, type) and issubclass(obj, Enum):
				return Shape._cast_plain_enum(obj)
			else:
				raise TypeError(f'Object {obj!r} cannot be converted to a Torii shape')
			if new_obj is obj:
				raise RecursionError(f'Shape-castable object {obj!r} casts to itself')
			obj = new_obj

	def __repr__(self) -> str:
		if self.signed:
			return f'signed({self.width})'
		else:
			return f'unsigned({self.width})'

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Shape):
			try:
				other = self.__class__.cast(other)
			except TypeError as e:
				raise TypeError(f'Shapes may be compared with shape-castable objects, not {other!r}') from e

		return self.width == other.width and self.signed == other.signed

class _ShapeLikeMeta(type):
	def __subclasscheck__(cls: type[T], subclass: type[U]) -> bool:
		return (
			issubclass(subclass, (Shape, ShapeCastable, int, range, EnumMeta)) or
			subclass is ShapeLike
		)

	def __instancecheck__(cls: type[T], instance: object) -> bool:
		if isinstance(instance, int):
			return instance >= 0
		if isinstance(instance, EnumMeta):
			# NOTE(aki): once again, because `Enum`/`EnumMeta` is untypable we can't properly type the `member.value`
			return all(isinstance(member.value, ValueLike) for member in instance) # type: ignore

		return isinstance(instance, (Shape, ShapeCastable, range))

@final
class ShapeLike(metaclass = _ShapeLikeMeta):
	'''
	An abstract class representing all objects that can be cast to a :class:`Shape`.

	``issubclass(cls, ShapeLike)`` returns ``True`` for:

	- :class:`Shape`
	- :class:`ShapeCastable` and its subclasses
	- ``int`` and its subclasses
	- ``range`` and its subclasses
	- :class:`enum.EnumMeta` and its subclasses
	- :class:`ShapeLike` itself

	``isinstance(obj, ShapeLike)`` returns ``True`` for:

	- :class:`Shape` instances
	- :class:`ShapeCastable` instances
	- non-negative ``int`` values
	- ``range`` instances
	- :class:`enum.Enum` subclasses where all values are :ref:`value-like <lang-valuelike>`

	This class is only usable for the above checks — no instances and no (non-virtual)
	subclasses can be created.
	'''

	def __new__(cls, *args, **kwargs):
		raise TypeError('ShapeLike is an abstract class and cannot be constructed')


def unsigned(width: int) -> Shape:
	''' Shorthand for ``Shape(width, signed = False)``. '''
	return Shape(width, signed = False)


def signed(width: int) -> Shape:
	''' Shorthand for ``Shape(width, signed = True)``. '''
	return Shape(width, signed = True)

def _overridable_by_swapping(method_name: str):
	'''
	Allow overriding the decorated method.

	Allows :class:`ValueCastable` to override the decorated method by implementing
	a reflected method named ``method_name``. Intended for operators, but
	also usable for other methods that have a reflected counterpart.
	'''
	def decorator(f: Callable[[T, U], ReturnType]) -> Callable[[T, U], ReturnType]:
		@functools.wraps(f)
		def wrapper(self: T, other: U) -> ReturnType:
			if isinstance(other, ValueCastable) and hasattr(other, method_name):
				res: ReturnType | NotImplementedType = getattr(other, method_name)(self)
				if res is not NotImplemented:
					if TYPE_CHECKING:
						assert not isinstance(res, NotImplementedType)

					return res
			return f(self, other)
		return wrapper
	return decorator

def _index_valuelike(value: 'Value | ValueCastable', key: object) -> 'Value':
	n = len(value)
	if isinstance(key, int):
		if key not in range(-n, n):
			raise IndexError(f'Index {key} is out of bounds for a {n}-bit value')
		if key < 0:
			key += n
		return Slice(value, key, key + 1, src_loc_at = 1)
	elif isinstance(key, slice):
		if isinstance(key.start, Value) or isinstance(key.stop, Value):
			raise SyntaxError(
				'Slicing a value with a Value is unsupported, '
				'use `Value.bit_select()` or `Value.word_select()` instead.'
			)
		start, stop, step = key.indices(n)
		if step != 1:
			return Cat(*(value[i] for i in range(start, stop, step)))
		return Slice(value, start, stop, src_loc_at = 1)
	elif isinstance(key, Value):
		raise SyntaxError('Indexing a value with another value is not supported, use `Value.bit_select()` instead.')
	else:
		raise TypeError(f'Cannot index value with {key!r}')

class Value(metaclass = ABCMeta):

	src_loc: tuple[str, int] | None

	@staticmethod
	def cast(obj: ValueCastT) -> 'Value':
		'''
		Converts ``obj`` to an Torii value.

		Booleans and integers are wrapped into a :class:`Const`. Enumerations whose members are
		all integers are converted to a :class:`Const` with a shape that fits every member.
		:class:`ValueCastable` objects are recursively cast to an Torii value.

		'''
		while True:
			if isinstance(obj, Value):
				return obj
			elif isinstance(obj, ValueCastable):
				# NOTE(aki): See TODO on `ValueCastable.__init_subclass__`
				new_obj = obj.as_value() # type: ignore
			elif isinstance(obj, Enum):
				return Const(obj.value, Shape.cast(type(obj)))
			elif isinstance(obj, int):
				return Const(obj)
			else:
				raise TypeError(f'Object {obj!r} cannot be converted to a Torii value')
			if new_obj is obj:
				raise RecursionError(f'Value-castable object {obj!r} casts to itself')
			obj = new_obj

	def __init__(self, *, src_loc_at: int = 0) -> None:
		super().__init__()
		self.src_loc = tracer.get_src_loc(1 + src_loc_at)

	def __bool__(self) -> None:
		raise TypeError('Attempted to convert Torii value to Python boolean')

	def __pos__(self) -> 'Value':
		return self

	def __invert__(self) -> 'Operator':
		return Operator('~', (self,))

	def __neg__(self) -> 'Operator':
		return Operator('-', (self,))

	@_overridable_by_swapping('__radd__')
	def __add__(self, other: ValueCastT) -> 'Operator':
		return Operator('+', (self, other), src_loc_at = 1)

	def __radd__(self, other: ValueCastT) -> 'Operator':
		return Operator('+', (other, self))

	@_overridable_by_swapping('__rsub__')
	def __sub__(self, other: ValueCastT) -> 'Operator':
		return Operator('-', (self, other), src_loc_at = 1)

	def __rsub__(self, other: ValueCastT) -> 'Operator':
		return Operator('-', (other, self))

	@_overridable_by_swapping('__rmul__')
	def __mul__(self, other: ValueCastT) -> 'Operator':
		return Operator('*', (self, other), src_loc_at = 1)

	def __rmul__(self, other: ValueCastT) -> 'Operator':
		return Operator('*', (other, self))

	@_overridable_by_swapping('__rmod__')
	def __mod__(self, other: ValueCastT) -> 'Operator':
		return Operator('%', (self, other), src_loc_at = 1)

	def __rmod__(self, other: ValueCastT) -> 'Operator':
		return Operator('%', (other, self))

	@_overridable_by_swapping('__rfloordiv__')
	def __floordiv__(self, other: ValueCastT) -> 'Operator':
		return Operator('//', (self, other), src_loc_at = 1)

	def __rfloordiv__(self, other: ValueCastT) -> 'Operator':
		return Operator('//', (other, self))


	def __check_shamt(self) -> None:
		if self.shape().signed:
			# Neither Python nor HDLs implement shifts by negative values; prohibit any shifts
			# by a signed value to make sure the shift amount can always be interpreted as
			# an unsigned value.
			raise TypeError('Shift amount must be unsigned')

	@_overridable_by_swapping('__rlshift__')
	def __lshift__(self, other: ValueCastT) -> 'Operator':
		other = Value.cast(other)
		other.__check_shamt()
		return Operator('<<', (self, other), src_loc_at = 1)

	def __rlshift__(self, other: ValueCastT) -> 'Operator':
		self.__check_shamt()
		return Operator('<<', (other, self))

	@_overridable_by_swapping('__rrshift__')
	def __rshift__(self, other: ValueCastT) -> 'Operator':
		other = Value.cast(other)
		other.__check_shamt()
		return Operator('>>', (self, other), src_loc_at = 1)

	def __rrshift__(self, other: ValueCastT) -> 'Operator':
		self.__check_shamt()
		return Operator('>>', (other, self))

	@_overridable_by_swapping('__rand__')
	def __and__(self, other: ValueCastT) -> 'Operator':
		return Operator('&', (self, other), src_loc_at = 1)

	def __rand__(self, other: ValueCastT) -> 'Operator':
		return Operator('&', (other, self))

	@_overridable_by_swapping('__rxor__')
	def __xor__(self, other: ValueCastT) -> 'Operator':
		return Operator('^', (self, other), src_loc_at = 1)

	def __rxor__(self, other: ValueCastT) -> 'Operator':
		return Operator('^', (other, self))

	@_overridable_by_swapping('__ror__')
	def __or__(self, other: ValueCastT) -> 'Operator':
		return Operator('|', (self, other), src_loc_at = 1)

	def __ror__(self, other: ValueCastT) -> 'Operator':
		return Operator('|', (other, self))

	@_overridable_by_swapping('__eq__')
	def __eq__(self, other: ValueCastT) -> 'Operator':
		return Operator('==', (self, other), src_loc_at = 1)

	@_overridable_by_swapping('__ne__')
	def __ne__(self, other: ValueCastT) -> 'Operator':
		return Operator('!=', (self, other), src_loc_at = 1)

	@_overridable_by_swapping('__gt__')
	def __lt__(self, other: ValueCastT) -> 'Operator':
		return Operator('<', (self, other), src_loc_at = 1)

	@_overridable_by_swapping('__ge__')
	def __le__(self, other: ValueCastT) -> 'Operator':
		return Operator('<=', (self, other), src_loc_at = 1)

	@_overridable_by_swapping('__lt__')
	def __gt__(self, other: ValueCastT) -> 'Operator':
		return Operator('>', (self, other), src_loc_at = 1)

	@_overridable_by_swapping('__le__')
	def __ge__(self, other: ValueCastT) -> 'Operator':
		return Operator('>=', (self, other), src_loc_at = 1)

	def __abs__(self) -> 'Value':
		if self.shape().signed:
			return Mux(self >= 0, self, -self)[:len(self)]
		else:
			return self

	def __len__(self) -> int:
		return self.shape().width

	def __getitem__(self, key: object) -> 'Value':
		return _index_valuelike(self, key)

	def __contains__(self, _):
		raise TypeError('The python `in` operator is not supported on Torii values')

	def as_unsigned(self)  -> 'Operator':
		'''
		Conversion to unsigned.

		Returns
		-------
		Value, out
			This ``Value`` reinterpreted as a unsigned integer.

		'''

		return Operator('u', (self,))

	def as_signed(self)  -> 'Operator':
		'''
		Conversion to signed.

		Returns
		-------
		Value, out
			This ``Value`` reinterpreted as a signed integer.

		'''
		if len(self) == 0:
			raise ValueError('Cannot create a 0-width signed value')
		return Operator('s', (self,))

	def bool(self)  -> 'Operator':
		'''
		Conversion to boolean.

		Returns
		-------
		Value, out
			``1`` if any bits are set, ``0`` otherwise.

		'''

		return Operator('b', (self,))

	def any(self)  -> 'Operator':
		'''
		Check if any bits are ``1``.

		Returns
		-------
		Value, out
			``1`` if any bits are set, ``0`` otherwise.

		'''

		return Operator('r|', (self,))

	def all(self)  -> 'Operator':
		'''
		Check if all bits are ``1``.

		Returns
		-------
		Value, out
			``1`` if all bits are set, ``0`` otherwise.

		'''

		return Operator('r&', (self,))

	def xor(self)  -> 'Operator':
		'''
		Compute pairwise exclusive-or of every bit.

		Returns
		-------
		Value, out
			``1`` if an odd number of bits are set, ``0`` if an even number of bits are set.

		'''

		return Operator('r^', (self,))

	def implies(premise, conclusion: ValueCastT)  -> 'Operator':
		'''
		Implication.

		Returns
		-------
		Value, out
			``0`` if ``premise`` is true and ``conclusion`` is not, ``1`` otherwise.

		'''

		op = ~premise | conclusion

		if TYPE_CHECKING:
			assert isinstance(op, Operator)

		return op

	def bit_select(self, offset: 'Value | int' , width: int) -> 'Value':
		'''
		Part-select with bit granularity.

		Selects a constant width but variable offset part of a ``Value``, such that successive
		parts overlap by all but 1 bit.

		Parameters
		----------
		offset : Value, int
			Index of first selected bit.
		width : int
			Number of selected bits.

		Returns
		-------
		Part, out
			Selected part of the ``Value``

		'''

		offset = Value.cast(offset)
		if type(offset) is Const and isinstance(width, int):
			return self[offset.value:offset.value + width]
		return Part(self, offset, width, stride = 1, src_loc_at = 1)

	def word_select(self, offset: 'Value | int' , width: int) -> 'Value':
		'''
		Part-select with word granularity.

		Selects a constant width but variable offset part of a ``Value``, such that successive
		parts do not overlap.

		Parameters
		----------
		offset : Value, int
			Index of first selected word.
		width : int
			Number of selected bits.

		Returns
		-------
		Part, out
			Selected part of the ``Value``

		'''

		offset = Value.cast(offset)
		if type(offset) is Const and isinstance(width, int):
			return self[offset.value * width:(offset.value + 1) * width]
		return Part(self, offset, width, stride = width, src_loc_at = 1)

	def matches(self, *patterns: int | str | EnumMeta) -> 'Value':
		'''
		Pattern matching.

		Matches against a set of patterns, which may be integers or bit strings, recognizing
		the same grammar as ``Case()``.

		Parameters
		----------
		patterns : int, str, or Enum
			Patterns to match against.

		Returns
		-------
		Value, out
			``1`` if any pattern matches the value, ``0`` otherwise.

		'''

		matches: list[Value] = []
		# This code should accept exactly the same patterns as `with m.Case(...):`.
		for pattern in patterns:
			if isinstance(pattern, str) and any(bit not in '01- \t' for bit in pattern):
				raise SyntaxError(
					f'Match pattern \'{pattern}\' must consist of 0, 1, and - (don\'t care) bits, and may include whitespace'
				)

			if (isinstance(pattern, str) and len(''.join(pattern.split())) != len(self)):
				raise SyntaxError(
					f'Match pattern \'{pattern}\' must have the same width as match value (which is {len(self)})'
				)

			if isinstance(pattern, str):
				pattern = ''.join(pattern.split()) # remove whitespace
				mask    = int(pattern.replace('0', '1').replace('-', '0'), 2)
				pattern = int(pattern.replace('-', '0'), 2)
				matches.append((self & mask) == pattern)
			else:
				try:
					# NOTE(aki): mypy has issues with this re-assignment, but it's fine
					new_pattern: Const = Const.cast(pattern)
				except TypeError as error:
					raise SyntaxError(
						'Match pattern must be a string or a const-castable expression, '
						f'not {pattern!r}'
					) from error

				pattern_len = bits_for(new_pattern.value)
				if pattern_len > len(self):
					warnings.warn(
						f'Match pattern \'{pattern}\' ({pattern_len}\'{new_pattern.value:b}) is wider than '
						f'match value (which has width {len(self)}); comparison will never be true',
						SyntaxWarning, stacklevel = 2
					)
					continue
				matches.append(self == new_pattern)

		if not matches:
			warnings.warn(
				'Value.matches() with an empty patterns clause will return `Const(0)` in a future release.',
				SyntaxWarning, stacklevel = 2
			)
			return Const(1)
		elif len(matches) == 1:
			return matches[0]
		else:
			return Cat(*matches).any()

	def shift_left(self, amount: int) -> 'Value':
		'''
		Shift left by constant amount.

		Parameters
		----------
		amount : int
			Amount to shift by.

		Returns
		-------
		Value, out
			If the amount is positive, the input shifted left. Otherwise, the input shifted right.

		'''

		if not isinstance(amount, int):
			raise TypeError(f'Shift amount must be an integer, not {amount!r}')
		if amount < 0:
			return self.shift_right(-amount)
		if self.shape().signed:
			return Cat(Const(0, amount), self).as_signed()
		else:
			return Cat(Const(0, amount), self) # unsigned

	def shift_right(self, amount: int) -> 'Value':
		'''
		Shift right by constant amount.

		Parameters
		----------
		amount : int
			Amount to shift by.

		Returns
		-------
		Value, out
			If the amount is positive, the input shifted right. Otherwise, the input shifted left.

		'''

		if not isinstance(amount, int):
			raise TypeError(f'Shift amount must be an integer, not {amount!r}')
		if amount < 0:
			return self.shift_left(-amount)
		if self.shape().signed:
			if amount >= len(self):
				amount = len(self) - 1
			return self[amount:].as_signed()
		else:
			return self[amount:] # unsigned

	def rotate_left(self, amount: int) -> 'Value':
		'''
		Rotate left by constant amount.

		Parameters
		----------
		amount : int
			Amount to rotate by.

		Returns
		-------
		Value, out
			If the amount is positive, the input rotated left. Otherwise, the input rotated right.

		'''

		if not isinstance(amount, int):
			raise TypeError(f'Rotate amount must be an integer, not {amount!r}')
		if len(self) != 0:
			amount %= len(self)
		return Cat(self[-amount:], self[:-amount]) # meow :3

	def rotate_right(self, amount: int) -> 'Value':
		'''
		Rotate right by constant amount.

		Parameters
		----------
		amount : int
			Amount to rotate by.

		Returns
		-------
		Value, out
			If the amount is positive, the input rotated right. Otherwise, the input rotated right.

		'''

		if not isinstance(amount, int):
			raise TypeError(f'Rotate amount must be an integer, not {amount!r}')
		if len(self) != 0:
			amount %= len(self)
		return Cat(self[amount:], self[:amount])

	def replicate(self, count: int) -> 'Value':
		'''
		Replication.

		A ``Value`` is replicated (repeated) several times to be used
		on the RHS of assignments::

			len(v.replicate(n)) == len(v) * n

		Parameters
		----------
		count : int
			Number of replications.

		Returns
		-------
		Value, out
			Replicated value.
		'''
		if not isinstance(count, int) or count < 0:
			raise TypeError(f'Replication count must be a non-negative integer, not {count!r}')
		return Cat(*(self for _ in range(count)))

	def eq(self, value: ValueCastT) -> 'Assign':
		'''
		Assignment.

		Parameters
		----------
		value : Value, in
			Value to be assigned.

		Returns
		-------
		Assign
			Assignment statement that can be used in combinatorial or synchronous context.

		'''

		return Assign(self, value, src_loc_at = 1)

	def inc(self, value: ValueCastT = 1) -> 'Assign':
		'''
		Increment value.

		This is shorthand for ``a.eq(a + n)``

		Parameters
		----------
		value : Value, in
			Value to increment by. (default: 1)

		Returns
		-------
		Assign
			Assignment statement that can be used in combinatorial or synchronous context.

		'''

		return Assign(self, self + value, src_loc_at = 1)

	def dec(self, value: ValueCastT = 1) -> 'Assign':
		'''
		Decrement value.

		This is shorthand for ``a.eq(a - n)``

		Parameters
		----------
		value : Value, in
			Value to decrement by. (default: 1)

		Returns
		-------
		Assign
			Assignment statement that can be used in combinatorial or synchronous context.

		'''

		return Assign(self, self - value, src_loc_at = 1)

	@abstractmethod
	def shape(self) -> Shape:
		'''
		Bit width and signedness of a value.

		Returns
		-------
		Shape
			See :class:`Shape`.

		Examples
		--------
		>>> Signal(8).shape()
		Shape(width = 8, signed = False)
		>>> Const(0xaa).shape()
		Shape(width = 8, signed = False)

		'''

		raise NotImplementedError('.shape has not been implemented')

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		raise TypeError(f'Value {self!r} cannot be used in assignments')

	@abstractmethod
	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		pass # :nocov:

class _ConstMeta(ABCMeta):
	def __call__(cls, value: int, shape: 'Shape | int | range | type | ShapeCastable | None' = None, src_loc_at: int = 0, **kwargs):
		if isinstance(shape, ShapeCastable):
			return shape.const(value)
		return super().__call__(value, shape, **kwargs, src_loc_at = src_loc_at + 1)

@final
class Const(Value, metaclass = _ConstMeta):
	'''
	A constant, literal integer value.

	Parameters
	----------
	value : int
	shape : int or tuple or None
		Either an integer ``width`` or a tuple ``(width, signed)`` specifying the number of bits
		in this constant and whether it is signed (can represent negative values).
		``shape`` defaults to the minimum possible width and signedness of ``value``.

	Attributes
	----------
	width : int
	signed : bool

	'''

	src_loc = None

	@staticmethod
	def normalize(value: int, shape: 'Shape') -> int:
		mask = (1 << shape.width) - 1
		value &= mask
		if shape.signed and (value >> (shape.width - 1)) & 1:
			value |= ~mask
		return value

	@staticmethod
	def cast(obj: ValueCastT) -> 'Const':
		'''
		Converts ``obj`` to an Torii constant.

		First, ``obj`` is converted to a value using :meth:`Value.cast`. If it is a constant, it
		is returned. If it is a constant-castable expression, it is evaluated and returned.
		Otherwise, :exn:`TypeError` is raised.
		'''

		obj = Value.cast(obj)
		if type(obj) is Const:
			return obj
		elif type(obj) is Cat:
			value = 0
			width = 0
			for part in obj.parts:
				const  = Const.cast(part)
				part_value = Const(const.value, unsigned(const.width)).value
				value |= part_value << width
				width += len(const)
			return Const(value, width)
		elif type(obj) is Slice:
			# NOTE(aki): mypy leaks type of `value` from above `elif`
			value = Const.cast(obj.value) # type: ignore

			# Do type coercion
			if TYPE_CHECKING:
				assert isinstance(value, Const)

			return Const(value.value >> obj.start, unsigned(obj.stop - obj.start))
		else:
			raise TypeError(f'Value {obj!r} cannot be converted to an Torii constant')


	def __init__(
		self, value: int, shape: 'Shape | int | range | type | ShapeCastable | None' = None, *,
		src_loc_at: int = 0
	) -> None:
		# We deliberately do not call Value.__init__ here.
		self.value = int(operator.index(value))
		if shape is None:
			shape = Shape(bits_for(self.value), signed = self.value < 0)
		elif isinstance(shape, int):
			shape = Shape(shape, signed = self.value < 0)
		else:
			if isinstance(shape, range) and self.value == shape.stop:
				warnings.warn(
					message =
						f'Value {self.value!r} equals the non-inclusive end of the constant '
						f'shape {shape!r}; this is likely an off-by-one error',
					category = SyntaxWarning,
					stacklevel = 3
				)
			shape = Shape.cast(shape, src_loc_at = 1 + src_loc_at)
		self.width  = shape.width
		self.signed = shape.signed
		self.value  = self.normalize(self.value, shape)

	def shape(self) -> Shape:
		return Shape(self.width, self.signed)

	def _rhs_signals(self) -> 'SignalSet':
		return SignalSet()

	def __repr__(self) -> str:
		return f'(const {self.width}\'{"s" if self.signed else ""}d{self.value})'


OperatorsT: TypeAlias = Literal[
	'+', '~', '-', 'b', 'r|', 'r&', 'r^', 'u', 's', '*', '//', '%',
	'<', '<=', '==', '!=', '>', '>=', '&', '^', '|', '<<', '>>', 'm'
]
@final
class Operator(Value):
	def __init__(self, operator: OperatorsT, operands: Sequence[ValueCastT] , *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = 1 + src_loc_at)
		self.operator = operator
		self.operands = [ Value.cast(op) for op in operands ]

	def shape(self) -> Shape:
		def _bitwise_binary_shape(a_shape: Shape, b_shape: Shape) -> Shape:
			if not a_shape.signed and not b_shape.signed:
				# both operands unsigned
				return unsigned(max(a_shape.width, b_shape.width))
			elif a_shape.signed and b_shape.signed:
				# both operands signed
				return signed(max(a_shape.width, b_shape.width))
			elif not a_shape.signed and b_shape.signed:
				# first operand unsigned (add sign bit), second operand signed
				return signed(max(a_shape.width + 1, b_shape.width))
			else:
				# first signed, second operand unsigned (add sign bit)
				return signed(max(a_shape.width, b_shape.width + 1))

		op_shapes = list(map(lambda x: x.shape(), self.operands))
		if len(op_shapes) == 1:
			a_shape, = op_shapes
			if self.operator in ('+', '~'):
				return Shape(a_shape.width, a_shape.signed)
			if self.operator == '-':
				return Shape(a_shape.width + 1, True)
			if self.operator in ('b', 'r|', 'r&', 'r^'):
				return Shape(1, False)
			if self.operator == 'u':
				return Shape(a_shape.width, False)
			if self.operator == 's':
				return Shape(a_shape.width, True)
		elif len(op_shapes) == 2:
			a_shape, b_shape = op_shapes
			if self.operator == '+':
				o_shape = _bitwise_binary_shape(*op_shapes)
				return Shape(o_shape.width + 1, o_shape.signed)
			if self.operator == '-':
				o_shape = _bitwise_binary_shape(*op_shapes)
				return Shape(o_shape.width + 1, True)
			if self.operator == '*':
				return Shape(a_shape.width + b_shape.width, a_shape.signed or b_shape.signed)
			if self.operator == '//':
				return Shape(a_shape.width + b_shape.signed, a_shape.signed or b_shape.signed)
			if self.operator == '%':
				return Shape(b_shape.width, b_shape.signed)
			if self.operator in ('<', '<=', '==', '!=', '>', '>='):
				return Shape(1, False)
			if self.operator in ('&', '^', '|'):
				return _bitwise_binary_shape(*op_shapes)
			if self.operator == '<<':
				if b_shape.signed:
					raise TypeError('Operator << operand must be unsigned!')

				return Shape(a_shape.width + 2 ** b_shape.width - 1, a_shape.signed)
			if self.operator == '>>':
				if b_shape.signed:
					raise TypeError('Operator >> operand must be unsigned!')

				return Shape(a_shape.width, a_shape.signed)
		elif len(op_shapes) == 3:
			if self.operator == 'm':
				s_shape, a_shape, b_shape = op_shapes
				return _bitwise_binary_shape(a_shape, b_shape)
		raise NotImplementedError(f'Operator {self.operator}/{len(op_shapes)} not implemented') # :nocov:

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		if self.operator in ('u', 's'):
			return union(op._lhs_signals() for op in self.operands)
		return super()._lhs_signals()

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		return union(op._rhs_signals() for op in self.operands)

	def __repr__(self) -> str:
		return f'({self.operator} {" ".join(map(repr, self.operands))})'


def Mux(sel: ValueCastT, val1: ValueCastT, val0: ValueCastT) -> Operator:
	'''
	Choose between two values.

	Parameters
	----------
	sel : Value, in
		Selector.
	val1 : Value, in
	val0 : Value, in
		Input values.

	Returns
	-------
	Value, out
		Output ``Value``. If ``sel`` is asserted, the Mux returns ``val1``, else ``val0``.

	'''

	return Operator('m', (sel, val1, val0))


@final
class Slice(Value):
	def __init__(
		self, value: ValueCastT, start: int, stop: int, *, src_loc_at: int = 0
	) -> None:
		if not isinstance(start, int):
			raise TypeError(f'Slice start must be an integer, not {start!r}')
		if not isinstance(stop, int):
			raise TypeError(f'Slice stop must be an integer, not {stop!r}')

		value = Value.cast(value)
		n = len(value)
		if start not in range(-n, n + 1):
			raise IndexError(f'Cannot start slice {start} bits into {n}-bit value')
		if start < 0:
			start += n
		if stop not in range(-n, n + 1):
			raise IndexError(f'Cannot stop slice {stop} bits into {n}-bit value')
		if stop < 0:
			stop += n
		if start > stop:
			raise IndexError(f'Slice start {start} must be less than slice stop {stop}')

		super().__init__(src_loc_at = src_loc_at)
		self.value = value
		self.start = int(operator.index(start))
		self.stop  = int(operator.index(stop))

	def shape(self) -> Shape:
		return Shape(self.stop - self.start)

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		return self.value._lhs_signals()

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		return self.value._rhs_signals()

	def __repr__(self) -> str:
		return f'(slice {repr(self.value)} {self.start}:{self.stop})'


@final
class Part(Value):
	def __init__(
		self, value: ValueCastT, offset: ValueCastT, width: int, stride: int = 1, *,
		src_loc_at: int = 0
	) -> None:
		if not isinstance(width, int) or width < 0:
			raise TypeError(f'Part width must be a non-negative integer, not {width!r}')
		if not isinstance(stride, int) or stride <= 0:
			raise TypeError(f'Part stride must be a positive integer, not {stride!r}')

		value  = Value.cast(value)
		offset = Value.cast(offset)
		if offset.shape().signed:
			raise TypeError('Part offset must be unsigned')

		super().__init__(src_loc_at = src_loc_at)
		self.value  = value
		self.offset = offset
		self.width  = width
		self.stride = stride

	def shape(self) -> Shape:
		return Shape(self.width)

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		return self.value._lhs_signals()

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		signals = self.value._rhs_signals() | self.offset._rhs_signals()

		if TYPE_CHECKING:
			assert isinstance(signals, (ValueSet, SignalSet))

		return signals

	def __repr__(self) -> str:
		return f'(part {repr(self.value)} {repr(self.offset)} {self.width} {self.stride})'


@final
class Cat(Value):
	'''
	Concatenate values.

	Form a compound ``Value`` from several smaller ones by concatenation.
	The first argument occupies the lower bits of the result.
	The return value can be used on either side of an assignment, that
	is, the concatenated value can be used as an argument on the RHS or
	as a target on the LHS. If it is used on the LHS, it must solely
	consist of ``Signal`` s, slices of ``Signal`` s, and other concatenations
	meeting these properties. The bit length of the return value is the sum of
	the bit lengths of the arguments::

		len(Cat(args)) == sum(len(arg) for arg in args)

	Parameters
	----------
	*args : Values or iterables of Values, inout
		``Value`` s to be concatenated.

	Returns
	-------
	Value, inout
		Resulting ``Value`` obtained by concatenation.

	'''

	def __init__(self, *args: 'ValueCastT | Iterable[ValueCastT]', src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)
		self.parts: list[Value] = []
		for index, arg in enumerate(flatten(args)):
			if isinstance(arg, Enum) and (not isinstance(type(arg), ShapeCastable) or not hasattr(arg, '_torii_shape_')):
				warnings.warn(
					f'Argument #{index + 1} of \'Cat()\' is an enumerated value {arg!r} without '
					'a defined shape used in a bit vector context; use \'Const\' to specify '
					'the shape.',
					SyntaxWarning, stacklevel = 2 + src_loc_at
				)

			if isinstance(arg, int) and not isinstance(arg, Enum) and arg not in [0, 1]:
				warnings.warn(
					f'Argument #{index + 1} of \'Cat()\' is a bare integer {arg} used in bit vector '
					f'context; consider specifying the width explicitly using \'Const({arg}, {bits_for(arg)})\' '
					'instead',
					SyntaxWarning, stacklevel = 2 + src_loc_at
				)

			# NOTE(aki): Type inference is scrambled by the check above, so as painful as it is we ignore it
			self.parts.append(Value.cast(arg)) # type: ignore

	def shape(self) -> Shape:
		return Shape(sum(len(part) for part in self.parts))

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		return union((part._lhs_signals() for part in self.parts), start = SignalSet())

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		return union((part._rhs_signals() for part in self.parts), start = SignalSet())

	def __repr__(self) -> str:
		return f'(cat {" ".join(map(repr, self.parts))})'


SignalAttrs: TypeAlias = dict[str, int | str | bool]
SignalDecoder: TypeAlias = Callable[[int], str] | type[Enum]
_SigParams = TypeVarTuple('_SigParams')
# @final
class Signal(Value, DUID, Generic[Unpack[_SigParams]]):
	'''
	A varying integer value.

	Parameters
	----------
	shape : ``Shape``-castable object or None
		Specification for the number of bits in this ``Signal`` and its signedness (whether it
		can represent negative values). See ``Shape.cast`` for details.
		If not specified, ``shape`` defaults to 1-bit and non-signed.
	name : str
		Name hint for this signal. If ``None`` (default) the name is inferred from the variable
		name this ``Signal`` is assigned to.
	reset : int or integral Enum
		Reset (synchronous) or default (combinatorial) value.
		When this ``Signal`` is assigned to in synchronous context and the corresponding clock
		domain is reset, the ``Signal`` assumes the given value. When this ``Signal`` is unassigned
		in combinatorial context (due to conditional assignments not being taken), the ``Signal``
		assumes its ``reset`` value. Defaults to 0.
	reset_less : bool
		If ``True``, do not generate reset logic for this ``Signal`` in synchronous statements.
		The ``reset`` value is only used as a combinatorial default or as the initial value.
		Defaults to ``False``.
	attrs : dict
		Dictionary of synthesis attributes.
	decoder : function or Enum
		A function converting integer signal values to human-readable strings (e.g. FSM state
		names). If an ``Enum`` subclass is passed, it is concisely decoded using format string
		``"{0.name:}/{0.value:}"``, or a number if the signal value is not a member of
		the enumeration.

	Attributes
	----------
	width : int
	signed : bool
	name : str
	reset : int
	reset_less : bool
	attrs : dict
	decoder : function

	'''

	decoder: Callable[[int], str] | None
	_enum_class: type[Enum] | None

	def __init__(
		self, shape: 'ShapeCastT | None' = None, *,
		name: str | None = None, reset: int | EnumMeta | None = None, reset_less: bool = False, attrs: SignalAttrs | None = None,
		decoder: SignalDecoder | None = None, src_loc_at: int = 0
	) -> None:
		super().__init__(src_loc_at = src_loc_at)

		if name is not None and not isinstance(name, str):
			raise TypeError(f'Name must be a string, not {name!r}')

		self.name = name or tracer.get_var_name(depth = 2 + src_loc_at, default = '$signal')

		orig_shape = shape
		if shape is None:
			shape = unsigned(1)
		else:
			shape = Shape.cast(shape, src_loc_at = 1 + src_loc_at)
		self.width  = shape.width
		self.signed = shape.signed

		if isinstance(orig_shape, ShapeCastable):
			try:
				reset_val = Const.cast(orig_shape.const(reset))
			except Exception:
				raise TypeError(
					f'Reset value must be a constant initializer of {orig_shape!r}'
				)

			if reset_val.shape() != Shape.cast(orig_shape):
				raise ValueError(
					f'Constant returned by {orig_shape!r}.const() must have the shape that it casts '
					f'to, {Shape.cast(orig_shape)!r}, and not {reset_val.shape()!r}'
				)
		else:
			try:
				reset_val = Const.cast(reset or 0)
			except TypeError:
				raise TypeError(
					f'Reset value must be a constant-castable expression, not {reset!r}'
				)

		# Avoid false positives for all-zeroes and all-ones
		if reset not in (None, 0, -1):
			if reset_val.shape().signed and not self.signed:
				warnings.warn(
					message = f'Reset value {reset!r} is signed, but the signal shape is {shape!r}',
					category = SyntaxWarning,
					stacklevel = 2
				)
			elif (
				reset_val.shape().width > self.width or
				reset_val.shape().width == self.width and
				self.signed and not reset_val.shape().signed
			):
				warnings.warn(
					message = f'Reset value {reset!r} will be truncated to the signal shape {shape!r}',
					category = SyntaxWarning,
					stacklevel = 2
				)
		self.reset = reset_val.value
		self.reset_less = bool(reset_less)

		if isinstance(orig_shape, range) and reset is not None and reset not in orig_shape:
			if reset == orig_shape.stop:
				raise SyntaxError(
					f'Reset value {reset!r} equals the non-inclusive end of the signal '
					f'shape {orig_shape!r}; this is likely an off-by-one error',
				)
			else:
				raise SyntaxError(f'Reset value {reset!r} is not within the signal shape {orig_shape!r}')

		self.attrs = OrderedDict(() if attrs is None else attrs)

		if decoder is None and isinstance(orig_shape, type) and issubclass(orig_shape, Enum):
			decoder = orig_shape

			if TYPE_CHECKING:
				assert isinstance(decoder, type) and issubclass(decoder, Enum)


		if isinstance(decoder, type) and issubclass(decoder, Enum):
			def enum_decoder(value: int) -> str:
				try:
					return '{0.name:}/{0.value:}'.format(decoder(value))
				except ValueError:
					return str(value)
			self.decoder = enum_decoder
			self._enum_class = decoder
		else:
			if TYPE_CHECKING:
				assert not isinstance(decoder, type)

			self.decoder = decoder
			self._enum_class = None

	# Not a @classmethod because torii.compat requires it.
	@staticmethod
	def like(
		other: 'Signal', *, name: str | None = None, name_suffix: str | None = None, src_loc_at: int = 0, **kwargs
	) -> 'Signal':
		'''
		Create Signal based on another.

		Parameters
		----------
		other : Value
			Object to base this Signal on.

		'''

		if name is not None:
			new_name = str(name)
		elif name_suffix is not None:
			new_name = other.name + str(name_suffix)
		else:
			new_name = tracer.get_var_name(depth = 2 + src_loc_at, default = '$like')

		if isinstance(other, ValueCastable):
			shape = other.shape()
		else:
			shape = Value.cast(other).shape()
		kw = dict(shape = shape, name = new_name)
		if isinstance(other, Signal):
			kw.update(
				reset = other.reset, reset_less = other.reset_less,
				attrs = other.attrs, decoder = other.decoder
			)
		kw.update(kwargs)
		# NOTE(aki): mypy will complain about this due to the param expansion
		return Signal(**kw, src_loc_at = 1 + src_loc_at) # type: ignore

	def shape(self) -> Shape:
		return Shape(self.width, self.signed)

	def _lhs_signals(self) -> 'SignalSet':
		return SignalSet((self,))

	def _rhs_signals(self) -> 'SignalSet':
		return SignalSet((self,))

	def __repr__(self) -> str:
		return f'(sig {self.name})'


@final
class ClockSignal(Value):
	'''
	Clock signal for a clock domain.

	Any ``ClockSignal`` is equivalent to ``cd.clk`` for a clock domain with the corresponding name.
	All of these signals ultimately refer to the same signal, but they can be manipulated
	independently of the clock domain, even before the clock domain is created.

	Parameters
	----------
	domain : str
		Clock domain to obtain a clock signal for. Defaults to ``'sync'``.

	'''

	def __init__(self, domain: str = 'sync', *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)
		if not isinstance(domain, str):
			raise TypeError(f'Clock domain name must be a string, not {domain!r}')
		if domain == 'comb':
			raise ValueError(f'Domain \'{domain}\' does not have a clock')
		self.domain = domain

	def shape(self) -> Shape:
		return Shape(1)

	def _lhs_signals(self) -> 'SignalSet':
		return SignalSet((self,))

	def _rhs_signals(self) -> NoReturn:
		raise NotImplementedError('ClockSignal must be lowered to a concrete signal') # :nocov:

	def __repr__(self) -> str:
		return f'(clk {self.domain})'


@final
class ResetSignal(Value):
	'''
	Reset signal for a clock domain.

	Any ``ResetSignal`` is equivalent to ``cd.rst`` for a clock domain with the corresponding name.
	All of these signals ultimately refer to the same signal, but they can be manipulated
	independently of the clock domain, even before the clock domain is created.

	Parameters
	----------
	domain : str
		Clock domain to obtain a reset signal for. Defaults to ``'sync'``.
	allow_reset_less : bool
		If the clock domain is reset-less, act as a constant ``0`` instead of reporting an error.

	'''

	def __init__(self, domain: str = 'sync', allow_reset_less: bool = False, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)
		if not isinstance(domain, str):
			raise TypeError(f'Clock domain name must be a string, not {domain!r}')
		if domain == 'comb':
			raise ValueError(f'Domain \'{domain}\' does not have a reset')
		self.domain = domain
		self.allow_reset_less = allow_reset_less

	def shape(self) -> Shape:
		return Shape(1)

	def _lhs_signals(self) -> 'SignalSet':
		return SignalSet((self,))

	def _rhs_signals(self) -> NoReturn:
		raise NotImplementedError('ResetSignal must be lowered to a concrete signal') # :nocov:

	def __repr__(self) -> str:
		return f'(rst {self.domain})'


@final
class AnyValue(Value, DUID):
	class Kind(Enum):
		AnyConst = 'anyconst'
		AnySeq   = 'anyseq'

	def __init__(self, kind: str, shape: ShapeCastable, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)

		self.kind   = self.Kind(kind)
		self._shape = Shape.cast(shape, src_loc_at = src_loc_at + 1)
		self.width  = self._shape.width
		self.signed = self._shape.signed

	def shape(self) -> Shape:
		return self._shape

	def _rhs_signals(self) -> 'SignalSet':
		return SignalSet()

	def __repr__(self) -> str:
		return f'({self.kind.value} {self.width}\'{"s" if self.signed else ""})'


def AnyConst(shape, *, src_loc_at: int = 0) -> AnyValue:
	return AnyValue('anyconst', shape, src_loc_at = src_loc_at + 1)

def AnySeq(shape, *, src_loc_at: int = 0) -> AnyValue:
	return AnyValue('anyseq', shape, src_loc_at = src_loc_at + 1)

class Array(MutableSequence[Value]):
	'''
	Addressable multiplexer.

	An array is similar to a ``list`` that can also be indexed by ``Value``s;
	indexing by an integer or a slice works the same as for Python lists,
	but indexing by a ``Value`` results in a proxy.

	The array proxy can be used as an ordinary ``Value``, i.e. participate in calculations and
	assignments, provided that all elements of the array are values. The array proxy also supports
	attribute access and further indexing, each returning another array proxy; this means that
	the results of indexing into arrays, arrays of records, and arrays of arrays can all
	be used as first-class values.

	It is an error to change an array or any of its elements after an array proxy was created.
	Changing the array directly will raise an exception. However, it is not possible to detect
	the elements being modified; if an element's attribute or element is modified after the proxy
	for it has been created, the proxy will refer to stale data.

	Examples
	--------

	Simple array::

		gpios = Array(Signal() for _ in range(10))
		with m.If(bus.we):
			m.d.sync += gpios[bus.addr].eq(bus.w_data)
		with m.Else():
			m.d.sync += bus.r_data.eq(gpios[bus.addr])

	Multidimensional array::

		mult = Array(Array(x * y for y in range(10)) for x in range(10))
		a = Signal.range(10)
		b = Signal.range(10)
		r = Signal(8)
		m.d.comb += r.eq(mult[a][b])

	Array of records::

		layout = [
			("r_data", 16),
			("r_en",   1),
		]
		buses  = Array(Record(layout) for busno in range(4))
		master = Record(layout)
		m.d.comb += [
			buses[sel].r_en.eq(master.r_en),
			master.r_data.eq(buses[sel].r_data),
		]

	'''

	_proxy_at: SrcLoc | None

	def __init__(self, iterable: Sequence[Value] = ()) -> None:
		self._inner    = list(iterable)
		self._proxy_at = None
		self._mutable  = True

	# NOTE(aki): We overload this method, so we need to shush the type checker
	def __getitem__(self, index: 'Value | ValueCastable | int') -> 'Value | ArrayProxy': # type: ignore
		if isinstance(index, ValueCastable):
			index = Value.cast(index)

		if isinstance(index, Value):
			if self._mutable:
				self._proxy_at = tracer.get_src_loc()
				self._mutable  = False
			return ArrayProxy(self, index)
		else:
			return self._inner[index]

	def __len__(self) -> int:
		return len(self._inner)

	def _check_mutability(self) -> None:
		if not self._mutable:
			if self._proxy_at is None:
				raise AttributeError('Array is not mutable, however no proxy location has been specified')

			filename, lineno = self._proxy_at
			raise ValueError(
				f'Array can no longer be mutated after it was indexed with a value at {filename}:{lineno}'
			)

	# NOTE(aki): The ignore on the type is because we're once again, overloading this method
	def __setitem__(self, index: int, value: Value) -> None: # type: ignore
		self._check_mutability()
		self._inner[index] = value

	def __delitem__(self, index: slice | int) -> None:
		self._check_mutability()
		del self._inner[index]

	def insert(self, index: SupportsIndex, value: Value) -> None:
		self._check_mutability()
		self._inner.insert(index, value)

	def __repr__(self) -> str:
		return f'(array{" mutable" if self._mutable else ""} [{", ".join(map(repr, self._inner))}])'

@final
class ArrayProxy(Value):
	def __init__(self, elems, index: ValueCastT, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = 1 + src_loc_at)
		self.elems = elems
		self.index = Value.cast(index)

	def __getattr__(self, attr) -> 'ArrayProxy':
		return ArrayProxy([getattr(elem, attr) for elem in self.elems], self.index)

	def __getitem__(self, index) -> 'ArrayProxy':
		return ArrayProxy([        elem[index] for elem in self.elems], self.index)

	def _iter_as_values(self):
		return (Value.cast(elem) for elem in self.elems)

	def shape(self) -> Shape:
		unsigned_width = signed_width = 0
		has_unsigned = has_signed = False
		for elem_shape in (elem.shape() for elem in self._iter_as_values()):
			if elem_shape.signed:
				has_signed = True
				signed_width = max(signed_width, elem_shape.width)
			else:
				has_unsigned = True
				unsigned_width = max(unsigned_width, elem_shape.width)
		# The shape of the proxy must be such that it preserves the mathematical value of the array
		# elements. I.e., shape-wise, an array proxy must be identical to an equivalent mux tree.
		# To ensure this holds, if the array contains both signed and unsigned values, make sure
		# that every unsigned value is zero-extended by at least one bit.
		if has_signed and has_unsigned and unsigned_width >= signed_width:
			# Array contains both signed and unsigned values, and at least one of the unsigned
			# values won't be zero-extended otherwise.
			return signed(unsigned_width + 1)
		else:
			# Array contains values of the same signedness, or else all of the unsigned values
			# are zero-extended.
			return Shape(max(unsigned_width, signed_width), has_signed)

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		signals = union((elem._lhs_signals() for elem in self._iter_as_values()), start = SignalSet())

		if TYPE_CHECKING:
			assert isinstance(signals, (ValueSet, SignalSet))

		return signals

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		signals = self.index._rhs_signals() | union(
			(elem._rhs_signals() for elem in self._iter_as_values()),
			start = SignalSet()
		)

		if TYPE_CHECKING:
			assert isinstance(signals, (ValueSet, SignalSet))

		return signals

	def __repr__(self) -> str:
		return f'(proxy (array [{", ".join(map(repr, self.elems))}]) {self.index!r})'

class ValueCastable:
	'''
	Interface of user-defined objects that can be cast to :class:`Value` s.

	An object deriving from :class:`ValueCastable`` is automatically converted to a :class:`Value`
	when it is used in a context where a :class:`Value`` is expected. Such objects can implement
	different or richer semantics than what is supported by the core Torii language, yet still
	be transparently used with it as long as the final underlying representation is a single
	Torii :class:`Value`. These objects also need not commit to a specific representation until
	they are converted to a concrete Torii value.

	Note that it is necessary to ensure that Torii's view of representation of all values stays
	internally consistent. The class deriving from :class:`ValueCastable`` must decorate
	the :meth:`as_value` method with the :meth:`lowermethod` decorator, which ensures that all
	calls to :meth:`as_value` return the same :class:`Value` representation. If the class deriving
	from :class:`ValueCastable` is mutable, it is up to the user to ensure that it is not mutated
	in a way that changes its representation after the first call to :meth:`as_value`.

	'''

	# TODO(aki): This check for `_ValueCastable__memoized` prevents us from being an ABC, so we need to figure out
	#            a sane way to keep that check but also let us properly type as_value and as_shape
	def __init_subclass__(cls, **kwargs):
		if not hasattr(cls, 'as_value'):
			raise TypeError(
				f'Class \'{cls.__name__}\' deriving from `ValueCastable` must override the `as_value` method'
			)
		if not hasattr(cls, 'shape'):
			raise TypeError(
				f'Class \'{cls.__name__}\' deriving from `ValueCastable` must override the `shape` method'
			)
		if not hasattr(cls.as_value, '_ValueCastable__memoized'):
			raise TypeError(
				f'Class \'{cls.__name__}\' deriving from `ValueCastable` must decorate '
				'the `as_value` method with the `ValueCastable.lowermethod` decorator'
			)

	@staticmethod
	def lowermethod(func):
		'''
		Decorator to memoize lowering methods.

		Ensures the decorated method is called only once, with subsequent method calls returning
		the object returned by the first first method call.

		This decorator is required to decorate the ``as_value`` method of ``ValueCastable``
		subclasses. This is to ensure that Torii's view of representation of all values stays
		internally consistent.

		'''

		@functools.wraps(func)
		def wrapper_memoized(self, *args, **kwargs):
			# Use `in self.__dict__` instead of `hasattr` to avoid interfering with custom
			# `__getattr__` implementations.
			if '_ValueCastable__lowered_to' not in self.__dict__:
				self.__lowered_to = func(self, *args, **kwargs)
			return self.__lowered_to
		setattr(wrapper_memoized, '_ValueCastable__memoized', True)
		return wrapper_memoized

	def __getitem__(self, key: object) -> 'ValueCastable | Value':
		return _index_valuelike(self, key)

	def __len__(self) -> int:
		raise NotImplementedError()


class _ValueLikeMeta(type):
	'''
	An abstract class representing all objects that can be cast to a :class:`Value`.

	``issubclass(cls, ValueLike)`` returns ``True`` for:

	- :class:`Value`
	- :class:`ValueCastable` and its subclasses
	- ``int`` and its subclasses
	- :class:`enum.Enum` subclasses where all values are :ref:`value-like <lang-valuelike>`
	- :class:`ValueLike` itself

	``isinstance(obj, ValueLike)`` returns the same value as ``issubclass(type(obj), ValueLike)``.

	This class is only usable for the above checks — no instances and no (non-virtual)
	subclasses can be created.
	'''

	def __subclasscheck__(cls, subclass):
		if issubclass(subclass, Enum):
			return isinstance(subclass, ShapeLike)

		return (
			issubclass(subclass, (Value, ValueCastable, int)) or
			subclass is ValueLike
		)

	def __instancecheck__(cls, instance):
		return issubclass(type(instance), cls)


@final
class ValueLike(metaclass = _ValueLikeMeta):
	def __new__(cls, *args, **kwargs):
		raise TypeError('ValueLike is an abstract class and cannot be constructed')

@final
class Sample(Value):
	'''
	Value from the past.

	A ``Sample`` of an expression is equal to the value of the expression ``clocks`` clock edges
	of the ``domain`` clock back. If that moment is before the beginning of time, it is equal
	to the value of the expression calculated as if each signal had its reset value.

	'''

	def __init__(self, expr: ValueCastT, clocks: int, domain: str | None, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = 1 + src_loc_at)
		self.value  = Value.cast(expr)
		self.clocks = int(clocks)
		self.domain = domain
		if not isinstance(self.value, (Const, Signal, ClockSignal, ResetSignal, Initial)):
			raise TypeError(f'Sampled value must be a signal or a constant, not {self.value!r}')
		if self.clocks < 0:
			raise ValueError(f'Cannot sample a value {-self.clocks} cycles in the future')
		if not (self.domain is None or isinstance(self.domain, str)):
			raise TypeError(f'Domain name must be a string or None, not {self.domain!r}')

	def shape(self) -> Shape:
		return self.value.shape()

	def _rhs_signals(self) -> 'ValueSet':
		return ValueSet((self,))

	def __repr__(self) -> str:
		return f'(sample {self.value!r} @ {"<default>" if self.domain is None else self.domain}[{self.clocks}])'


def Past(expr: ValueCastT, clocks: int = 1, domain: str | None = None) -> Value:
	return Sample(expr, clocks, domain)


# NOTE(aki): For Stable, Rose, and Fell, mypy can't see through the operators
def Stable(expr: ValueCastT, clocks: int = 0, domain: str | None = None) -> Operator:
	op = Sample(expr, clocks + 1, domain) == Sample(expr, clocks, domain)

	if TYPE_CHECKING:
		assert isinstance(op, Operator)

	return op


def Rose(expr: ValueCastT, clocks: int = 0, domain: str | None = None) -> Operator:
	op = ~Sample(expr, clocks + 1, domain) & Sample(expr, clocks, domain)

	if TYPE_CHECKING:
		assert isinstance(op, Operator)

	return op


def Fell(expr: ValueCastT, clocks: int = 0, domain: str | None = None) -> Operator:
	op = Sample(expr, clocks + 1, domain) & ~Sample(expr, clocks, domain)

	if TYPE_CHECKING:
		assert isinstance(op, Operator)

	return op


@final
class Initial(Value):
	'''
	Start indicator, for model checking.

	An ``Initial`` signal is ``1`` at the first cycle of model checking, and ``0`` at any other.

	'''

	def __init__(self, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)

	def shape(self) -> Shape:
		return Shape(1)

	def _rhs_signals(self) -> 'ValueSet':
		return ValueSet((self,))

	def __repr__(self) -> str:
		return '(initial)'


class _StatementList(list['Statement']):
	def __repr__(self) -> str:
		return f'({" ".join(map(repr, self))})'


class Statement:
	def __init__(self, *, src_loc_at: int = 0) -> None:
		self.src_loc = tracer.get_src_loc(1 + src_loc_at)

	@staticmethod
	def cast(obj: 'Iterable | Statement'):
		if isinstance(obj, Iterable):
			return _StatementList(list(chain.from_iterable(map(Statement.cast, obj))))
		else:
			if isinstance(obj, Statement):
				return _StatementList([obj])
			else:
				raise TypeError(f'Object {obj!r} is not an Torii statement')


@final
class Assign(Statement):
	def __init__(self, lhs: ValueCastT, rhs: ValueCastT, *, src_loc_at: int = 0) -> None:
		super().__init__(src_loc_at = src_loc_at)
		self.lhs = Value.cast(lhs)
		self.rhs = Value.cast(rhs)

	def _lhs_signals(self) -> 'ValueSet | SignalSet':
		return self.lhs._lhs_signals()

	def _rhs_signals(self) -> 'ValueSet | SignalSet':
		signals = self.lhs._rhs_signals() | self.rhs._rhs_signals()

		if TYPE_CHECKING:
			assert isinstance(signals, (ValueSet, SignalSet))

		return signals

	def __repr__(self) -> str:
		return f'(eq {self.lhs!r} {self.rhs!r})'


class UnusedProperty(UnusedMustUse):
	pass


@final
class Property(Statement, MustUse):
	_MustUse__warning = UnusedProperty

	class Kind(Enum):
		Assert = 'assert'
		Assume = 'assume'
		Cover  = 'cover'


	def __init__(
		self, kind: str, test: ValueCastT, *, _check: Signal | None = None, _en: Signal | None = None,
		name: str | None = None, src_loc_at: int = 0
	) -> None:
		super().__init__(src_loc_at = src_loc_at)
		self.kind   = self.Kind(kind)
		self.test   = Value.cast(test)

		self.name   = name

		if not isinstance(self.name, str) and self.name is not None:
			raise TypeError(f'Property name must be a string of None, not {self.name!r}')

		if _check is None:
			self._check: Signal = Signal(reset_less = True, name = f'${self.kind.value}$check')
			self._check.src_loc = self.src_loc
		else:
			self._check = _check

		if _en is None:
			self._en: Signal = Signal(reset_less = True, name = f'${self.kind.value}$en')
			self._en.src_loc = self.src_loc
		else:
			self._en = _en

	def _lhs_signals(self) -> 'SignalSet':
		return SignalSet((self._en, self._check))

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		return self.test._rhs_signals()

	def __repr__(self) -> str:
		if self.name is not None:
			return f'({self.name}: {self.kind.value} {self.test!r})'
		return f'({self.kind.value} {self.test!r})'


def Assert(test: ValueCastT, *, name: str | None = None, src_loc_at: int = 0) -> Property:
	return Property('assert', test, name = name, src_loc_at = src_loc_at + 1)

def Assume(test: ValueCastT, *, name: str | None = None, src_loc_at: int = 0) -> Property:
	return Property('assume', test, name = name, src_loc_at = src_loc_at + 1)

def Cover(test: ValueCastT, *, name: str | None = None, src_loc_at: int = 0) -> Property:
	return Property('cover', test, name = name, src_loc_at = src_loc_at + 1)

# @final
class Switch(Statement):
	def __init__(self, test: ValueCastT, cases: Mapping[SwitchCaseT, Iterable[object] | _StatementList], *,
		src_loc: SrcLoc | None = None, src_loc_at: int = 0, case_src_locs: dict[SwitchCaseT, SrcLoc] = {}
	) -> None:
		if src_loc is None:
			super().__init__(src_loc_at = src_loc_at)
		else:
			# Switch is a bit special in terms of location tracking because it is usually created
			# long after the control has left the statement that directly caused its creation.
			self.src_loc = src_loc
		# Switch is also a bit special in that its parts also have location information. It can't
		# be automatically traced, so whatever constructs a Switch may optionally provide it.
		self.case_src_locs: dict[tuple[str, ...], SrcLoc] = {}

		self.test  = Value.cast(test)
		self.cases = OrderedDict[tuple[str, ...], _StatementList]()
		for orig_keys, stmts in cases.items():
			# Map: None -> (); key -> (key,); (key...) -> (key...)
			if orig_keys is None:
				keys = tuple[SwitchCaseT, ...]()
			elif not isinstance(orig_keys, tuple):
				keys = (orig_keys,)
			else:
				keys = orig_keys
			# Map: 2 -> "0010"; "0010" -> "0010"
			new_keys = tuple[str, ...]()
			key_mask = (1 << len(self.test)) - 1
			for key in keys:
				if isinstance(key, str):
					new_key = ''.join(key.split()) # remove whitespace
				elif isinstance(key, int):
					new_key = format(key & key_mask, 'b').rjust(len(self.test), '0')
					if key_mask == 0:
						new_key = ''
				elif isinstance(key, Enum):
					new_key = format(key.value & key_mask, 'b').rjust(len(self.test), '0')
					if key_mask == 0:
						new_key = ''
				else:
					raise TypeError(f'Object {key!r} cannot be used as a switch key')
				if len(new_key) != len(self.test):
					raise ValueError(f'Length mismatch between switch key and test value {len(new_key)} != {len(self.test)}')
				new_keys = (*new_keys, new_key)
			if not isinstance(stmts, Iterable):
				stmts = [stmts]
			self.cases[new_keys] = Statement.cast(stmts)
			if orig_keys in case_src_locs:
				self.case_src_locs[new_keys] = case_src_locs[orig_keys]

	def _lhs_signals(self) -> 'SignalSet | ValueSet':
		signals = union((s._lhs_signals() for ss in self.cases.values() for s in ss), start = SignalSet())

		if TYPE_CHECKING:
			assert isinstance(signals, (SignalSet, ValueSet))

		return signals

	def _rhs_signals(self) -> 'SignalSet | ValueSet':
		signals = self.test._rhs_signals() | union(
			(s._rhs_signals() for ss in self.cases.values() for s in ss),
			start = SignalSet()
		)

		if TYPE_CHECKING:
			assert isinstance(signals, (SignalSet, ValueSet))

		return signals

	def __repr__(self) -> str:
		def case_repr(keys, stmts):
			stmts_repr = ' '.join(map(repr, stmts))
			if keys == ():
				return f'(default {stmts_repr})'
			elif len(keys) == 1:
				return f'(case {keys[0]} {stmts_repr})'
			else:
				return f'(case ({" ".join(keys)}) {stmts_repr})'
		case_reprs = [ case_repr(keys, stmts) for keys, stmts in self.cases.items() ]
		return f'(switch {self.test!r} {" ".join(case_reprs)})'

Key    = TypeVar('Key')
IntKey = TypeVar('IntKey', bound = 'SignalKey | ValueKey')
Val    = TypeVar('Val')

class _MappedKeyCollection(Generic[IntKey, Key], metaclass = ABCMeta):
	''' Turn a normally non-key item, a `Signal` or `Value` into a `SignalKey` or `ValueKey` for collection indexing '''

	@abstractmethod
	def _map_key(self, key: Key) -> IntKey:
		''' Map the incoming key of type V to a `SignalKey` or `ValueKey` '''
		pass # :nocov:

	@abstractmethod
	def _unmap_key(self, key: IntKey) -> Key:
		''' Extract the `Signal` or `Value` from the key object '''
		pass # :nocov:


class _MappedKeyDict(MutableMapping[Key | None, Val], _MappedKeyCollection[IntKey, Key]):
	def __init__(self, pairs: tuple[tuple[Key, Val], ...] = ()):
		self._storage = OrderedDict[IntKey | None, Val]()
		for key, value in pairs:
			self[key] = value

	def __getitem__(self, key: Key | None) -> Val:
		if key is not None:
			internal_key = self._map_key(key)
		else:
			internal_key = None
		return self._storage[internal_key]

	def __setitem__(self, key: Key | None, value: Val) -> None:
		if key is not None:
			internal_key = self._map_key(key)
		else:
			internal_key = None

		self._storage[internal_key] = value


	def __delitem__(self, key: Key | None) -> None:
		if key is not None:
			internal_key = self._map_key(key)
		else:
			internal_key = None

		del self._storage[internal_key]

	def __iter__(self) -> Iterator[Key | None]:
		for internal_key in self._storage:
			if internal_key is None:
				yield None
			else:
				yield self._unmap_key(internal_key)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, type(self)):
			return False
		if len(self) != len(other):
			return False
		# NOTE(aki): ValueKey and SignalKey /should/ be Rich Comparison viable, but mypy just can't see it
		for ak, bk in zip(sorted(self._storage), sorted(other._storage)): # type: ignore
			if ak != bk:
				return False
			if self._storage[ak] != other._storage[bk]:
				return False
		return True

	def __len__(self) -> int:
		return len(self._storage)

	def __repr__(self) -> str:
		pairs = [ f'({k!r}, {v!r})' for k, v in self.items() ]
		return f'{type(self).__module__}.{type(self).__name__}([{", ".join(pairs)}])'


class _MappedKeySet(MutableSet[Key], _MappedKeyCollection[IntKey, Key]):
	def __init__(self, elements: Iterable[Key] = ()) -> None:
		self._storage = OrderedDict[IntKey, None]()
		for elem in elements:
			self.add(elem)

	def add(self, key: Key) -> None:
		self._storage[self._map_key(key)] = None

	def update(self, keys: Iterable[Key]) -> None:
		for key in keys:
			self.add(key)

	def discard(self, key: Key) -> None:
		if key in self:
			del self._storage[self._map_key(key)]

	def __contains__(self, key: object) -> bool:
		try:
			# NOTE(aki): The only real solution here it to give up and explode and ignore the type error
			return self._map_key(key) in self._storage # type: ignore
		except TypeError:
			return False

	def __iter__(self) -> Generator[Key]:
		for internal_key in [ int_k for int_k in self._storage ]:
			yield self._unmap_key(internal_key)

	def __len__(self) -> int:
		return len(self._storage)

	def __repr__(self) -> str:
		return f'{type(self).__module__}.{type(self).__name__}({", ".join(repr(x) for x in self)})'


class ValueKey:
	def __init__(self, value: ValueCastT) -> None:
		self.value = Value.cast(value)
		if isinstance(self.value, Const):
			self._hash = hash(self.value.value)
		elif isinstance(self.value, (Signal, AnyValue)):
			self._hash = hash(self.value.duid)
		elif isinstance(self.value, (ClockSignal, ResetSignal)):
			self._hash = hash(self.value.domain)
		elif isinstance(self.value, Operator):
			self._hash = hash((
				self.value.operator,
				tuple(ValueKey(o) for o in self.value.operands)
			))
		elif isinstance(self.value, Slice):
			self._hash = hash((ValueKey(self.value.value), self.value.start, self.value.stop))
		elif isinstance(self.value, Part):
			self._hash = hash((
				ValueKey(self.value.value), ValueKey(self.value.offset),
				self.value.width, self.value.stride
			))
		elif isinstance(self.value, Cat):
			self._hash = hash(tuple(ValueKey(o) for o in self.value.parts))
		elif isinstance(self.value, ArrayProxy):
			self._hash = hash((
				ValueKey(self.value.index),
				tuple(ValueKey(e) for e in self.value._iter_as_values())
			))
		elif isinstance(self.value, Sample):
			self._hash = hash((ValueKey(self.value.value), self.value.clocks, self.value.domain))
		elif isinstance(self.value, Initial):
			self._hash = 0
		else: # :nocov:
			raise TypeError(f'Object {self.value!r} cannot be used as a key in value collections')

	def __hash__(self) -> int:
		return self._hash

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, ValueKey):
			return False
		if not isinstance(self.value, type(other.value)):
			return False

		if isinstance(self.value, Const):
			assert isinstance(self.value, Const)
			assert isinstance(other.value, Const)
			return (
				self.value.value == other.value.value and
				self.value.width == other.value.width
			)
		elif isinstance(self.value, (Signal, AnyValue)):
			return self.value is other.value
		elif isinstance(self.value, (ClockSignal, ResetSignal)):
			assert isinstance(self.value, (ClockSignal, ResetSignal))
			assert isinstance(other.value, (ClockSignal, ResetSignal))
			return self.value.domain == other.value.domain
		elif isinstance(self.value, Operator):
			assert isinstance(self.value, Operator)
			assert isinstance(other.value, Operator)
			return (
				self.value.operator == other.value.operator and
				len(self.value.operands) == len(other.value.operands) and
				all(
					ValueKey(a) == ValueKey(b)
					for a, b in zip(self.value.operands, other.value.operands)
				)
			)
		elif isinstance(self.value, Slice):
			assert isinstance(self.value, Slice)
			assert isinstance(other.value, Slice)
			return (
				ValueKey(self.value.value) == ValueKey(other.value.value) and
				self.value.start == other.value.start and
				self.value.stop == other.value.stop
			)
		elif isinstance(self.value, Part):
			assert isinstance(self.value, Part)
			assert isinstance(other.value, Part)
			return (
				ValueKey(self.value.value) == ValueKey(other.value.value) and
				ValueKey(self.value.offset) == ValueKey(other.value.offset) and
				self.value.width == other.value.width and
				self.value.stride == other.value.stride
			)
		elif isinstance(self.value, Cat):
			assert isinstance(self.value, Cat)
			assert isinstance(other.value, Cat)
			return (
				len(self.value.parts) == len(other.value.parts) and
				all(
					ValueKey(a) == ValueKey(b)
					for a, b in zip(self.value.parts, other.value.parts)
				)
			)
		elif isinstance(self.value, ArrayProxy):
			assert isinstance(self.value, ArrayProxy)
			assert isinstance(other.value, ArrayProxy)
			return (
				ValueKey(self.value.index) == ValueKey(other.value.index) and
				len(self.value.elems) == len(other.value.elems) and
				all(
					ValueKey(a) == ValueKey(b)
					for a, b in zip(self.value._iter_as_values(), other.value._iter_as_values())
				)
			)
		elif isinstance(self.value, Sample):
			assert isinstance(self.value, Sample)
			assert isinstance(other.value, Sample)
			return (
				ValueKey(self.value.value) == ValueKey(other.value.value) and
				self.value.clocks == other.value.clocks and
				self.value.domain == self.value.domain
			)
		elif isinstance(self.value, Initial):

			return True
		else: # :nocov:
			raise TypeError(f'Object {self.value!r} cannot be used as a key in value collections')

	def __lt__(self, other: 'ValueKey') -> bool | Operator:
		if not isinstance(other, ValueKey):
			return False
		if not isinstance(self.value, type(other.value)):
			return False

		if isinstance(self.value, Const):
			assert isinstance(other.value, Const)
			result = self.value < other.value
			assert isinstance(result, Operator)
			return result
		elif isinstance(self.value, (Signal, AnyValue)):
			assert isinstance(other.value, (Signal, AnyValue))
			return self.value.duid < other.value.duid
		elif isinstance(self.value, Slice):
			assert isinstance(other.value, Slice)
			return (
				ValueKey(self.value.value) < ValueKey(other.value.value) and
				self.value.start < other.value.start and
				self.value.stop < other.value.stop
			)
		else: # :nocov:
			raise TypeError(f'Object {other!r} cannot be used as a key in value collections')

	def __repr__(self) -> str:
		return f'<{__name__}.ValueKey {self.value!r}>'


class ValueDict(_MappedKeyDict[Value, Val, ValueKey]):
	''' Mapping of `Value` objects to arbitrary value types '''

	def _map_key(self, key: Value) -> ValueKey:
		return ValueKey(key)

	def _unmap_key(self, key: ValueKey) -> Value:
		return key.value

class ValueSet(_MappedKeySet[Value, ValueKey]):
	''' Collection of unique `Value` objects '''

	def _map_key(self, key: Value) -> ValueKey:
		return ValueKey(key)

	def _unmap_key(self, key: ValueKey) -> Value:
		return key.value

SignalLikeT: TypeAlias = Signal | ClockSignal | ResetSignal

class SignalKey:
	'''
	Allow aliasing of the same internal signal in a design from multiple object instances.


	This allows you to map them as the same key in the resolution collections.

	Doing so allows for multiple instances of, say, a ``ClockSignal`` with the same domain to
	refer internally to the same signal upon design flatting.

	Meaning that wherever there is a ``ClockSignal('sync')`` they all refer to the same internal
	signal ID.

	'''

	_intern: tuple[Literal[0], int] | tuple[Literal[1, 2], str]

	def __init__(self, signal: SignalLikeT) -> None:
		self.signal = signal
		if isinstance(signal, Signal):
			self._intern = (0, signal.duid)
		elif type(signal) is ClockSignal:
			self._intern = (1, signal.domain)
		elif type(signal) is ResetSignal:
			self._intern = (2, signal.domain)
		else:
			raise TypeError(f'Object {signal!r} is not an Torii signal')

	def __hash__(self) -> int:
		return hash(self._intern)

	def __eq__(self, other: object) -> bool:
		if type(other) is not SignalKey:
			return False
		return self._intern == other._intern

	def __lt__(self, other: object) -> bool:
		if type(other) is not SignalKey:
			raise TypeError(f'Object {other!r} cannot be compared to a SignalKey')
		# NOTE(aki): This comparison works fine, but typing is having a hard time seeing through it
		return self._intern < other._intern # type: ignore

	def __repr__(self) -> str:
		return f'<{__name__}.SignalKey {self.signal!r}>'


class SignalDict(_MappedKeyDict[SignalLikeT, Val, SignalKey]):
	''' Mapping of `Signal` objects to arbitrary value types '''

	def _map_key(self, key: SignalLikeT | None) -> SignalKey:
		if key is None:
			raise TypeError('Key to SignalDict must not be None')

		return SignalKey(key)

	def _unmap_key(self, key: SignalKey) -> SignalLikeT:
		return key.signal


class SignalSet(_MappedKeySet[SignalLikeT | None, SignalKey]):
	''' Collection of unique `Signal` objects '''

	def _map_key(self, key: SignalLikeT | None) -> SignalKey:
		if key is None:
			raise TypeError('Key to SignalSet must not be None')

		return SignalKey(key)

	def _unmap_key(self, key: SignalKey) -> SignalLikeT:
		return key.signal
