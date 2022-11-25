# SPDX-License-Identifier: BSD-2-Clause

from collections import OrderedDict
from typing      import (
	Literal, Optional, Tuple, Union, Generator,
	Iterator, List, Dict, Callable
)

__all__ = (
	'Pins',
	'PinsN',
	'DiffPairs',
	'DiffPairsN',
	'Attrs',
	'Clock',
	'Subsignal',
	'Resource',
	'Connector',
)

class Pins:
	def __init__(
		self, names : str, *, dir : Literal['i', 'o', 'io', 'oe'] = 'io', invert : bool = False,
		conn : Optional[Tuple[str, Union[int, str]]] = None, assert_width : Optional[int] = None
	) -> None:
		if not isinstance(names, str):
			raise TypeError(f'Names must be a whitespace-separated string, not {names!r}')
		names = names.split()

		if conn is not None:
			conn_name, conn_number = conn
			if not (isinstance(conn_name, str) and isinstance(conn_number, (int, str))):
				raise TypeError(
					'Connector must be None or a pair of string (connector name) and '
					f'integer/string (connector number), not {conn!r}'
				)
			names = [ f'{conn_name}_{conn_number}:{name}' for name in names ]

		if dir not in ('i', 'o', 'io', 'oe'):
			raise TypeError(f'Direction must be one of \'i\', \'o\', \'oe\', or \'io\', not {dir!r}')

		if assert_width is not None and len(names) != assert_width:
			raise AssertionError(f'{len(names)} names are specified ({" ".join(names)}), but {assert_width} names are expected')

		self.names  = names
		self.dir    = dir
		self.invert = bool(invert)

	def __len__(self) -> int:
		return len(self.names)

	def __iter__(self) -> Iterator[str]:
		return iter(self.names)

	def map_names(self, mapping : Dict[str, str], resource) -> List[str]:
		mapped_names = []
		for name in self.names:
			while ":" in name:
				if name not in mapping:
					raise NameError(f'Resource {resource!r} refers to nonexistent connector pin {name}')
				name = mapping[name]
			mapped_names.append(name)
		return mapped_names

	def __repr__(self) -> str:
		return f'(pins{"-n" if self.invert else ""} {self.dir} {" ".join(self.names)})'


def PinsN(*args, **kwargs) -> Pins:
	return Pins(*args, invert = True, **kwargs)


class DiffPairs:
	def __init__(
		self, p : str, n : str, *, dir : Literal['i', 'o', 'io', 'oe'] = 'io', invert : bool = False,
		conn : Optional[Tuple[str, Union[int, str]]] = None, assert_width : Optional[bool] = None
	) -> None:
		self.p = Pins(p, dir = dir, conn = conn, assert_width = assert_width)
		self.n = Pins(n, dir = dir, conn = conn, assert_width = assert_width)

		if len(self.p.names) != len(self.n.names):
			raise TypeError(f'Positive and negative pins must have the same width, but {self.p!r} '
							f'and {self.n!r} do not')

		self.dir    = dir
		self.invert = bool(invert)

	def __len__(self) -> int:
		return len(self.p.names)

	def __iter__(self) -> Iterator[Tuple[str, str]]:
		return zip(self.p.names, self.n.names)

	def __repr__(self) -> str:
		return f'(diffpairs{"-n" if self.invert else ""} {self.dir} (p {" ".join(self.p.names)}) (n {" ".join(self.n.names)}))'


def DiffPairsN(*args, **kwargs) -> DiffPairs:
	return DiffPairs(*args, invert = True, **kwargs)


class Attrs(OrderedDict):
	def __init__(self, **attrs : Dict[str, Union[int, str, Callable]]) -> None:
		for key, value in attrs.items():
			if not (value is None or isinstance(value, (str, int)) or hasattr(value, '__call__')):
				raise TypeError(f'Value of attribute {key} must be None, int, str, or callable, not {value!r}')

		super().__init__(**attrs)

	def __repr__(self) -> str:
		items = []
		for key, value in self.items():
			if value is None:
				items.append('!' + key)
			else:
				items.append(key + '=' + repr(value))
		return f'(attrs {" ".join(items)})'


class Clock:
	def __init__(self, frequency : Union[float, int]) -> None:
		if not isinstance(frequency, (float, int)):
			raise TypeError('Clock frequency must be a number')

		self.frequency = float(frequency)

	@property
	def period(self) -> float:
		return 1 / self.frequency

	def __repr__(self) -> str:
		return f'(clock {self.frequency})'


class Subsignal:
	def __init__(
		self, name : str, *args : Union[Pins, DiffPairs, 'Subsignal', Attrs, Clock]
	) -> None:
		self.name  = name
		self.ios   = []
		self.attrs = Attrs()
		self.clock = None

		if not args:
			raise ValueError('Missing I/O constraints')
		for arg in args:
			if isinstance(arg, (Pins, DiffPairs)):
				if not self.ios:
					self.ios.append(arg)
				else:
					raise TypeError(
						'Pins and DiffPairs are incompatible with other location or '
						f'subsignal constraints, but {arg!r} appears after {self.ios[-1]!r}'
					)

			elif isinstance(arg, Subsignal):
				if not self.ios or isinstance(self.ios[-1], Subsignal):
					self.ios.append(arg)
				else:
					raise TypeError(
						'Subsignal is incompatible with location constraints, but '
						f'{arg!r} appears after {self.ios[-1]!r}'
					)
			elif isinstance(arg, Attrs):
				self.attrs.update(arg)
			elif isinstance(arg, Clock):
				if self.ios and isinstance(self.ios[-1], (Pins, DiffPairs)):
					if self.clock is None:
						self.clock = arg
					else:
						raise ValueError('Clock constraint can be applied only once')
				else:
					raise TypeError(f'Clock constraint can only be applied to Pins or DiffPairs, not {self.ios[-1]!r}')
			else:
				raise TypeError(f'Constraint must be one of Pins, DiffPairs, Subsignal, Attrs, or Clock, not {arg!r}')

	def _content_repr(self) -> str:
		parts = []
		for io in self.ios:
			parts.append(repr(io))
		if self.clock is not None:
			parts.append(repr(self.clock))
		if self.attrs:
			parts.append(repr(self.attrs))
		return " ".join(parts)

	def __repr__(self) -> str:
		return f'(subsignal {self.name} {self._content_repr()})'

class Resource(Subsignal):
	@classmethod
	def family(
		cls, name_or_number : Union[str, int], number : Optional[int] = None, *,
		ios : List[Union[Pins, DiffPairs, 'Subsignal', Attrs, Clock]], default_name : str, name_suffix : str = ''
	) -> 'Resource':
		# This constructor accepts two different forms:
		#  1. Number-only form:
		#       Resource.family(0, default_name = "name", ios = [ Pins("A0 A1") ])
		#  2. Name-and-number (name override) form:
		#       Resource.family("override", 0, default_name = "name", ios = ...)
		# This makes it easier to build abstractions for resources, e.g. an SPIResource abstraction
		# could simply delegate to `Resource.family(*args, default_name="spi", ios=ios)`.
		# The name_suffix argument is meant to support creating resources with
		# similar names, such as spi_flash, spi_flash_2x, etc.
		if name_suffix:  # Only add "_" if we actually have a suffix.
			name_suffix = '_' + name_suffix

		if number is None: # name_or_number is number
			return cls(default_name + name_suffix, name_or_number, *ios)
		else: # name_or_number is name
			return cls(name_or_number + name_suffix, number, *ios)

	def __init__(
		self, name : str, number : int, *args : Union[Pins, DiffPairs, 'Subsignal', Attrs, Clock]
	) -> None:
		if not isinstance(number, int):
			raise TypeError(f'Resource number must be an integer, not {number!r}')

		super().__init__(name, *args)
		self.number = number

	def __repr__(self) -> str:
		return f'(resource {self.name} {self.number} {self._content_repr()})'

class Connector:
	def __init__(
		self, name : str, number : int, io : Union[str, Dict[str, str]], *, conn : Optional[Tuple[str, Union[int, str]]] = None
	) -> None:
		self.name    = name
		self.number  = number
		mapping = OrderedDict()

		if isinstance(io, dict):
			for conn_pin, plat_pin in io.items():
				if not isinstance(conn_pin, str):
					raise TypeError(f'Connector pin name must be a string, not {conn_pin!r}')
				if not isinstance(plat_pin, str):
					raise TypeError(f'Platform pin name must be a string, not {plat_pin!r}')
				mapping[conn_pin] = plat_pin

		elif isinstance(io, str):
			for conn_pin, plat_pin in enumerate(io.split(), start = 1):
				if plat_pin == '-':
					continue

				mapping[str(conn_pin)] = plat_pin
		else:
			raise TypeError(f'Connector I/Os must be a dictionary or a string, not {io!r}')

		if conn is not None:
			conn_name, conn_number = conn
			if not (isinstance(conn_name, str) and isinstance(conn_number, (int, str))):
				raise TypeError('Connector must be None or a pair of string (connector name) and '
								f'integer/string (connector number), not {conn!r}')

			for conn_pin, plat_pin in mapping.items():
				mapping[conn_pin] = f'{conn_name}_{conn_number}:{plat_pin}'
		self.mapping = mapping

	def __repr__(self) -> str:
		return f'(connector {self.name} {self.number} {" ".join(f"{conn}=>{plat}" for conn, plat in self.mapping.items())})'

	def __len__(self) -> int:
		return len(self.mapping)

	def __iter__(self) -> Generator[Tuple[str, str], None, None]:
		for conn_pin, plat_pin in self.mapping.items():
			yield f'{self.name}_{self.number}:{conn_pin}', plat_pin
