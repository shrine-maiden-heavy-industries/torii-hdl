# SPDX-License-Identifier: BSD-2-Clause

from collections     import OrderedDict
from collections.abc import Iterable, Generator
from enum            import Enum, unique, auto, EnumMeta
from functools       import reduce, wraps
from typing          import Any, get_args, get_origin, TypeAlias
from inspect         import get_annotations, isclass

from ..util          import tracer, union
from .ast            import Cat, Shape, Signal, SignalSet, Value, ValueCastable, ShapeCastT

__all__ = (
	'DIR_FANIN',
	'DIR_FANOUT',
	'DIR_NONE',

	'Direction',
	'Layout',
	'Record',
)

@unique
class Direction(Enum):
	''' Signal/Subsignal Direction '''

	NONE   = auto()
	FANOUT = auto()
	FANIN  = auto()

DIR_NONE   = Direction.NONE
''' An alias for ``Direction.NONE`` '''
DIR_FANOUT = Direction.FANOUT
''' An alias for ``Direction.FANOUT`` '''
DIR_FANIN  = Direction.FANIN
''' An alias for ``Direction.FANIN`` '''

LayoutFieldT: TypeAlias = 'Iterable[tuple[str, LayoutFieldT | ShapeCastT] | tuple[str, Layout | ShapeCastT, Direction]] | Layout'

class Layout:
	@staticmethod
	def cast(obj: LayoutFieldT, *, src_loc_at: int = 0) -> 'Layout':
		if isinstance(obj, Layout):
			return obj
		return Layout(obj, src_loc_at = 1 + src_loc_at)

	def __init__(self, fields: LayoutFieldT, *, src_loc_at: int = 0) -> None:
		self.fields = OrderedDict[str, tuple['Layout | ShapeCastT', Direction]]()
		for field in fields:
			if not isinstance(field, tuple) or len(field) not in (2, 3):
				raise TypeError(f'Field {field!r} has invalid layout: should be either (name, shape) or (name, shape, direction)')
			if len(field) == 2:
				name, layout = field
				direction = DIR_NONE
				if isinstance(layout, Iterable) and not isinstance(layout, (Layout, EnumMeta, range, str)):
					shape: 'Layout | ShapeCastT' = Layout.cast(layout)
				else:
					shape = layout
			else:
				name, shape, direction = field
				if not isinstance(direction, Direction):
					raise TypeError(f'Field {field!r} has invalid direction: should be a Direction instance like DIR_FANIN')
			if not isinstance(name, str):
				raise TypeError(f'Field {field!r} has invalid name: should be a string')
			if not isinstance(shape, Layout):
				try:
					# Check provided shape by calling Shape.cast and checking for exception
					Shape.cast(shape, src_loc_at = 1 + src_loc_at)
				except Exception:
					raise TypeError(
						f'Field {field!r} has invalid shape: should be castable to Shape or a list of ''fields of a nested record'
					)
			if name in self.fields:
				raise NameError(f'Field {field!r} has a name that is already present in the layout')
			self.fields[name] = (shape, direction)

	def __getitem__(self, item: object) -> LayoutFieldT:
		if not isinstance(item, (str, Iterable)):
			raise TypeError()

		if not isinstance(item, str):
			return Layout([
				(name, shape, dir)
				for (name, (shape, dir)) in self.fields.items()
				if name in item
			])

		return self.fields[item]

	def __iter__(self) -> Generator[tuple[str, 'Layout | ShapeCastT', Direction]]:
		for name, (shape, dir) in self.fields.items():
			yield (name, shape, dir)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Layout):
			return False
		return self.fields == other.fields

	def __repr__(self) -> str:
		field_reprs = []
		for name, shape, dir in self:
			if dir == DIR_NONE:
				field_reprs.append(f'({name!r}, {shape!r})')
			else:
				field_reprs.append(f'({name!r}, {shape!r}, Direction.{dir.name})')
		return f'Layout([{", ".join(field_reprs)}])'


class Record(ValueCastable):
	_annotations: dict[str, Any]

	@staticmethod
	def like(other: 'Record', *, name = None, name_suffix = None, src_loc_at = 0) -> 'Record':
		if name is not None:
			new_name = str(name)
		elif name_suffix is not None:
			new_name = other.name + str(name_suffix)
		else:
			new_name = tracer.get_var_name(depth = 2 + src_loc_at, default = None)

		def concat(a: str | None, b: str) -> str:
			if a is None:
				return b
			return f'{a}__{b}'

		fields = dict[str, Record | Signal]()
		for field_name in other.fields:
			field = other[field_name]
			if isinstance(field, Record):
				fields[field_name] = Record.like(
					field, name = concat(new_name, field_name),
					src_loc_at = 1 + src_loc_at
				)
			else:
				assert isinstance(field, Signal)
				fields[field_name] = Signal.like(
					field, name = concat(new_name, field_name),
					src_loc_at = 1 + src_loc_at
				)

		return Record(other.layout, name = new_name, fields = fields, src_loc_at = 1)

	def __init_subclass__(cls, /, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._annotations = get_annotations(cls)

	def _extract_layout(self, annotations: dict[str, Any]) -> LayoutFieldT:
		layout = list[tuple[str, 'LayoutFieldT'] | tuple[str, 'Layout', Direction]]()
		for name, typ in annotations.items():
			# We have nested records
			if isclass(typ) and issubclass(typ, Record):
				layout.append(
					(name, self._extract_layout(get_annotations(typ)))
				)
			elif isinstance(get_origin(typ), type(Signal)):
				params = get_args(typ)
				if len(params) == 1:
					layout.append(
						(name, params[0], DIR_NONE)
					)
				elif len(params) == 2:
					layout.append(
						(name, params[0], params[1])
					)
		return layout

	def __init__(
		self, layout: 'LayoutFieldT | None' = None, *, name: str | None = None, fields = None, src_loc_at: int = 0
	) -> None:
		if name is None:
			name = tracer.get_var_name(depth = 2 + src_loc_at, default = None)

		self.name    = name
		self.src_loc = tracer.get_src_loc(src_loc_at)

		def concat(a: str | None, b: str) -> str:
			if a is None:
				return b
			return f'{a}__{b}'

		if layout is None:
			if len(self._annotations) > 0:
				layout = self._extract_layout(self._annotations)
			else:
				raise ValueError('No layout specified and unable to construct one from type annotations')

		self.layout = Layout.cast(layout, src_loc_at = 1 + src_loc_at)
		self.fields = OrderedDict[str, Record | Signal]()
		for field_name, field_shape, field_dir in self.layout:
			if fields is not None and field_name in fields:
				field = fields[field_name]
				if isinstance(field_shape, Layout):
					assert isinstance(field, Record) and field_shape == field.layout
				else:
					assert isinstance(field, Signal) and Shape.cast(field_shape) == field.shape()
				self.fields[field_name] = field
			else:
				if isinstance(field_shape, Layout):
					self.fields[field_name] = Record(
						field_shape, name = concat(name, field_name),
						src_loc_at = 1 + src_loc_at
					)
				else:
					self.fields[field_name] = Signal(
						field_shape, name = concat(name, field_name),
						src_loc_at = 1 + src_loc_at
					)

	def __getattr__(self, name: str):
		# TODO: Add tests for this!
		if name == 'fields' and name not in self.__dict__:
			raise AssertionError('Record has not been properly constructed and does not have any fields')
		return self[name]

	def __getitem__(self, item: object) -> 'ValueCastable | Value':
		if isinstance(item, str):
			try:
				return self.fields[item]
			except KeyError:
				if self.name is None:
					reference = 'Unnamed record'
				else:
					reference = f'Record \'{self.name}\''
				raise AttributeError(
					f'{reference} does not have a field \'{item}\'. Did you mean one of: {", ".join(self.fields)}?'
				) from None
		elif isinstance(item, tuple):
			return Record(self.layout[item], fields = {
				field_name: field_value
				for field_name, field_value in self.fields.items()
				if field_name in item
			})
		else:
			try:
				return super().__getitem__(item)
			except KeyError:
				if self.name is None:
					reference = 'Unnamed record'
				else:
					reference = f'Record \'{self.name}\''
				raise AttributeError(
					f'{reference} does not have a field \'{item}\'. Did you mean one of: {", ".join(self.fields)}?'
				) from None

	@ValueCastable.lowermethod
	def as_value(self) -> Cat:
		return Cat(self.fields.values())

	def __len__(self) -> int:
		return len(self.as_value())

	def _lhs_signals(self):
		return union((f._lhs_signals() for f in self.fields.values()), start = SignalSet())

	def _rhs_signals(self):
		return union((f._rhs_signals() for f in self.fields.values()), start = SignalSet())

	def __repr__(self) -> str:
		fields = []
		for field_name, field in self.fields.items():
			if isinstance(field, Signal):
				fields.append(field_name)
			else:
				fields.append(repr(field))
		name = self.name
		if name is None:
			name = '<unnamed>'
		return f'(rec {name} {" ".join(fields)})'

	def shape(self):
		return self.as_value().shape()

	def connect(self, *subordinates, include = None, exclude = None):
		def rec_name(record):
			if record.name is None:
				return 'unnamed record'
			else:
				return f'record \'{record.name}\''

		for field in include or {}:
			if field not in self.fields:
				raise AttributeError(f'Cannot include field \'{field}\' because it is not present in {rec_name(self)}')

		for field in exclude or {}:
			if field not in self.fields:
				raise AttributeError(f'Cannot exclude field \'{field}\' because it is not present in {rec_name(self)}')

		stmts = []
		for field in self.fields:
			if include is not None and field not in include:
				continue
			if exclude is not None and field in exclude:
				continue

			shape, direction = self.layout[field]
			if not isinstance(shape, Layout) and direction == DIR_NONE:
				raise TypeError(f'Cannot connect field \'{field}\' of {rec_name(self)} because it does not have a direction')


			item = self.fields[field]
			subord_items = []
			for subord in subordinates:
				if field not in subord.fields:
					raise AttributeError(
						f'Cannot connect field \'{field}\' of {rec_name(self)} to subordinate '
						f'{rec_name(subord)} because the subordinate record does not have this field'
					)
				subord_items.append(subord.fields[field])

			if isinstance(shape, Layout):
				sub_include = include[field] if include and field in include else None
				sub_exclude = exclude[field] if exclude and field in exclude else None
				stmts += item.connect(*subord_items, include = sub_include, exclude = sub_exclude)
			else:
				if direction == DIR_FANOUT:
					stmts += [ sub_item.eq(item) for sub_item in subord_items ]
				if direction == DIR_FANIN:
					stmts += [ item.eq(reduce(lambda a, b: a | b, subord_items)) ]

		return stmts

def _valueproxy(name):
	value_func = getattr(Value, name)

	@wraps(value_func)
	def _wrapper(self, *args, **kwargs):
		return value_func(Value.cast(self), *args, **kwargs)

	return _wrapper

for name in [
		'__bool__',
		'__invert__', '__neg__',
		'__add__', '__radd__', '__sub__', '__rsub__',
		'__mul__', '__rmul__',
		'__mod__', '__rmod__', '__floordiv__', '__rfloordiv__',
		'__lshift__', '__rlshift__', '__rshift__', '__rrshift__',
		'__and__', '__rand__', '__xor__', '__rxor__', '__or__', '__ror__',
		'__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__',
		'__abs__', '__len__',
		'as_unsigned', 'as_signed', 'bool', 'any', 'all', 'xor', 'implies',
		'bit_select', 'word_select', 'matches',
		'shift_left', 'shift_right', 'rotate_left', 'rotate_right', 'eq'
]:
	setattr(Record, name, _valueproxy(name))

del _valueproxy
del name
