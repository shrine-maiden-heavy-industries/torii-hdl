# SPDX-License-Identifier: BSD-2-Clause

from __future__      import annotations

from collections     import OrderedDict
from collections.abc import Callable, Generator, Iterator, Sequence
from typing          import TypeAlias
from warnings        import warn

from .._typing       import IODirectionOE
from ..diagnostics   import ToriiSyntaxError
from ..hdl.time      import Period, Frequency, GHz, kHz, MHz
from ..util.tracer   import get_src_loc

__all__ = (
	'Attrs',
	'Clock',
	'Connector',
	'DiffPairs',
	'DiffPairsN',
	'Pins',
	'PinsN',
	'Resource',
	'Subsignal',
)

ResourceConn: TypeAlias = tuple[str, str | int]

class Pins:
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, pins: str, *, dir: IODirectionOE = 'io', invert: bool = False, conn: ResourceConn | None = None,
		assert_width: int | None = None, src_loc_at: int = 0
	) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		if not isinstance(pins, str):
			raise ToriiSyntaxError(
				f'Names must be a whitespace-separated string, not {pins!r}',
				src_loc = self.src_loc
			)

		names: list[str] = pins.split()

		if conn is not None:
			conn_name, conn_number = conn
			if not (isinstance(conn_name, str) and isinstance(conn_number, (int, str))):
				raise ToriiSyntaxError(
					'Connector must be None or a pair of string (connector name) and '
					f'integer/string (connector number), not {conn!r}',
					src_loc = self.src_loc
				)
			names = [ f'{conn_name}_{conn_number}:{name}' for name in names ]

		if dir not in ('i', 'o', 'io', 'oe'):
			raise ToriiSyntaxError(
				f'Direction must be one of \'i\', \'o\', \'oe\', or \'io\', not {dir!r}',
				src_loc = self.src_loc
			)

		if assert_width is not None and len(names) != assert_width:
			raise ToriiSyntaxError(
				f'{len(names)} pin(s) are specified ({" ".join(names)}), but {assert_width} pin(s) are expected',
				src_loc = self.src_loc
			)

		self.names  = names
		self.dir    = dir
		self.invert = bool(invert)

	def __len__(self) -> int:
		return len(self.names)

	def __iter__(self) -> Iterator[str]:
		return iter(self.names)

	def map_names(self, mapping: dict[str, str], resource) -> list[str]:
		'''
		.. todo:: Document Me
		'''

		mapped_names: list[str] = []
		for name in self.names:
			while ':' in name:
				if name not in mapping:
					# TODO(aki): ensure `resource` is always a `Resource`, then we can clean this up
					raise ToriiSyntaxError(
						f'Resource {resource!r} refers to nonexistent connector pin {name}',
						src_loc = self.src_loc
					)
				name = mapping[name]
			mapped_names.append(name)
		return mapped_names

	def __repr__(self) -> str:
		return f'(pins{"-n" if self.invert else ""} {self.dir} {" ".join(self.names)})'

def PinsN(
	names: str, *, dir: IODirectionOE = 'io', conn: ResourceConn | None = None, assert_width: int | None = None,
	src_loc_at: int = 0
) -> Pins:
	'''
	.. todo:: Document Me
	'''

	return Pins(
		names, dir = dir, invert = True, conn = conn, assert_width = assert_width, src_loc_at = src_loc_at + 1
	)

class DiffPairs:
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, p: str, n: str, *, dir: IODirectionOE = 'io', invert: bool = False, conn: ResourceConn | None = None,
		assert_width: int | None = None, src_loc_at: int = 0
	) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		self.p = Pins(p, dir = dir, conn = conn, assert_width = assert_width, src_loc_at = src_loc_at + 1)
		self.n = Pins(n, dir = dir, conn = conn, assert_width = assert_width, src_loc_at = src_loc_at + 1)

		if len(self.p.names) != len(self.n.names):
			more_or_fewer = 'more' if len(self.p.names) > len(self.n.names) else 'fewer'

			raise ToriiSyntaxError(
				'Differential pairs must have a symmetric set of positive and negative pins, however '
				f'{more_or_fewer} positive than negative pins were specified',
				src_loc = self.src_loc,
				notes = [
					f'The following positive pins were specified: {", ".join(self.p.names)}',
					f'The following negative pins were specified: {", ".join(self.n.names)}',
				]
			)

		self.dir    = dir
		self.invert = bool(invert)

	def __len__(self) -> int:
		return len(self.p.names)

	def __iter__(self) -> Iterator[tuple[str, str]]:
		return zip(self.p.names, self.n.names)

	def __repr__(self) -> str:
		return (
			f'(diffpairs{"-n" if self.invert else ""} {self.dir} '
			f'(p {" ".join(self.p.names)}) (n {" ".join(self.n.names)}))'
		)

def DiffPairsN(
	p: str, n: str, *, dir: IODirectionOE = 'io', conn: ResourceConn | None = None, assert_width: int | None = None,
	src_loc_at: int = 0
) -> DiffPairs:
	'''
	.. todo:: Document Me
	'''

	return DiffPairs(
		p = p, n = n, dir = dir, invert = True, conn = conn, assert_width = assert_width, src_loc_at = src_loc_at + 1
	)

class Attrs(OrderedDict[str, int | str | Callable]):
	'''
	.. todo:: Document Me
	'''

	def __init__(self, *, src_loc_at: int = 0, **attrs: int | str | Callable) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		for key, value in attrs.items():
			if not (value is None or isinstance(value, (str, int)) or hasattr(value, '__call__')):
				raise ToriiSyntaxError(
					f'Value of attribute {key} must be None, int, str, or callable, not {value!r}',
					src_loc = self.src_loc
				)

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
	'''
	Specify that this subsignal is a clock with a given frequency.

	Attributes
	----------
	frequency: torii.hdl.time.Frequency
		The frequency of this clock in Hertz.

	period: torii.hdl.time.Period
		The period of this clock in nanoseconds.

	Parameters
	----------
	frequency: torii.hdl.time.Frequency
		The frequency of this clock in Hertz.
	'''

	def __init__(self, frequency: Frequency | float | int, *, src_loc_at: int = 0) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		if isinstance(frequency, (float, int)):
			warn(
				f'Please use a `torii.hdl.time.Frequency` rather than a {type(frequency)} when specifying Clocks',
				DeprecationWarning,
				stacklevel = 2
			)
			self.frequency = Frequency(float(frequency))
		elif isinstance(frequency, Frequency):
			self.frequency = frequency
		else:
			raise ToriiSyntaxError(
				f'Clock frequency must be a `torii.hdl.time.Frequency`, a `float` or an `int`, not an {type(frequency)}'
			)

	@classmethod
	def from_khz(cls: type['Clock'], frequency: float | int) -> 'Clock':
		'''
		Create a new Clock resource with the given frequency in kHz.

		Warning
		-------
		This method is deprecated.

		Parameters
		----------
		frequency: float | int
			The frequency of the clock in kilohertz.

		Returns
		-------
		Clock
			An new clock at the given frequency in kilohertz.
		'''

		warn(
			'Please use the `Clock` constructor with a `torii.hdl.time.Frequency` over this method.',
			DeprecationWarning,
			stacklevel = 2
		)

		return Clock(frequency * kHz, src_loc_at = 1)

	@classmethod
	def from_mhz(cls: type['Clock'], frequency: float | int) -> 'Clock':
		'''
		Create a new Clock resource with the given frequency in MHz.

		Warning
		-------
		This method is deprecated.

		Parameters
		----------
		frequency: float | int
			The frequency of the clock in megahertz.

		Returns
		-------
		Clock
			A new clock at the given frequency in megahertz.
		'''

		warn(
			'Please use the `Clock` constructor with a `torii.hdl.time.Frequency` over this method.',
			DeprecationWarning,
			stacklevel = 2
		)

		return Clock(frequency * MHz, src_loc_at = 1)

	@classmethod
	def from_ghz(cls: type['Clock'], frequency: float | int) -> 'Clock':
		'''
		Create a new Clock resource with the given frequency in GHz.

		Warning
		-------
		This method is deprecated.

		Parameters
		----------
		frequency: float | int
			The frequency of the clock in gigahertz.

		Returns
		-------
		Clock
			A new clock at the given frequency in gigahertz.
		'''

		warn(
			'Please use the `Clock` constructor with a `torii.hdl.time.Frequency` over this method.',
			DeprecationWarning,
			stacklevel = 2
		)

		return Clock(frequency * GHz, src_loc_at = 1)

	@property
	def period(self) -> Period:
		'''
		.. todo:: Document Me
		'''

		return self.frequency.period

	def __repr__(self) -> str:
		return f'(clock {self.frequency!r})'

SubsigArgT: TypeAlias = 'Pins | DiffPairs | Subsignal | Attrs | Clock'

class Subsignal:
	'''
	.. todo:: Document Me
	'''

	def __init__(self, name: str, *args: SubsigArgT, src_loc_at: int = 0) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		self.name                  = name
		self.ios: list[SubsigArgT] = []
		self.attrs                 = Attrs()
		self.clock: Clock | None   = None

		_subsig_names = set[str]()

		if not args:
			raise ToriiSyntaxError(
				'Missing I/O constraints', src_loc = self.src_loc
			)
		for arg in args:
			if isinstance(arg, (Pins, DiffPairs)):
				if not self.ios:
					self.ios.append(arg)
				else:
					# TODO(aki): Figure out how to clean up this message and make it better
					raise ToriiSyntaxError(
						'Pins and DiffPairs are incompatible with other location or '
						f'subsignal constraints, but {arg!r} appears after {self.ios[-1]!r}',
						src_loc = self.src_loc
					)

			elif isinstance(arg, Subsignal):
				if not self.ios or isinstance(self.ios[-1], Subsignal):
					if arg.name in _subsig_names:
						# TODO(aki): Do we want to track src locs here? I don't think so
						raise ToriiSyntaxError(
							f'Attempted to add subsignal `{arg.name}` to `{self.name}` but a subsignal with that name'
							' already exists.',
							src_loc = self.src_loc,
						)

					_subsig_names.add(arg.name)
					self.ios.append(arg)
				else:
					# TODO(aki): Figure out how to clean up this message and make it better
					raise ToriiSyntaxError(
						'Subsignal is incompatible with location constraints, but '
						f'{arg!r} appears after {self.ios[-1]!r}',
						src_loc = self.src_loc
					)
			elif isinstance(arg, Attrs):
				self.attrs.update(arg)
			elif isinstance(arg, Clock):
				if self.ios and isinstance(self.ios[-1], (Pins, DiffPairs)):
					if self.clock is None:
						self.clock = arg
					else:
						raise ToriiSyntaxError(
							'Clock constraint can be applied only once', src_loc = self.src_loc
						)
				else:
					raise ToriiSyntaxError(
						f'Clock constraint can only be applied to Pins or DiffPairs, not {self.ios[-1]!r}',
						src_loc = self.src_loc
					)
			else:
				raise ToriiSyntaxError(
					f'Constraint must be one of Pins, DiffPairs, Subsignal, Attrs, or Clock, not {arg!r}',
					src_loc = self.src_loc
				)

	def _content_repr(self) -> str:
		parts: list[str] = []

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
	'''
	.. todo:: Document Me
	'''

	@classmethod
	def family(
		cls: type[Resource],
		name_or_number: str | int, number: int | None = None, *,
		ios: Sequence[SubsigArgT], default_name: str, name_suffix: str = '',
		src_loc_at: int = 0
	) -> Resource:
		'''
		.. todo:: Document Me
		'''

		# This constructor accepts two different forms:
		#  1. Number-only form:
		#       Resource.family(0, default_name = 'name', ios = [ Pins('A0 A1') ])
		#  2. Name-and-number (name override) form:
		#       Resource.family('override', 0, default_name = "name", ios = ...)
		# This makes it easier to build abstractions for resources, e.g. an SPIResource abstraction
		# could simply delegate to `Resource.family(*args, default_name = 'spi', ios = ios)`.
		# The name_suffix argument is meant to support creating resources with
		# similar names, such as spi_flash, spi_flash_2x, etc.
		if name_suffix:  # Only add '_' if we actually have a suffix.
			name_suffix = '_' + name_suffix

		# NOTE(aki): The type ignores here are silly but unless we do extra work to coerce the
		#            `name_or_number` type due to the silly call then mypy will forever complain
		if number is None: # name_or_number is number
			return cls(default_name + name_suffix, name_or_number, *ios, src_loc_at = 1 + src_loc_at) # type: ignore
		else: # name_or_number is name
			return cls(name_or_number + name_suffix, number, *ios, src_loc_at = 1 + src_loc_at) # type: ignore

	def __init__(self, name: str, number: int, *args: SubsigArgT, src_loc_at: int = 0) -> None:
		self.src_loc = get_src_loc(src_loc_at)

		if not isinstance(number, int):
			raise ToriiSyntaxError(
				f'Resource number must be an integer, not {number!r}',
				src_loc = self.src_loc
			)

		super().__init__(name, *args, src_loc_at = src_loc_at + 1)
		self.number = number

	def __repr__(self) -> str:
		return f'(resource {self.name} {self.number} {self._content_repr()})'

class Connector:
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, name: str, number: int, io: str | dict[str, str], *, conn: ResourceConn | None = None,
		src_loc_at: int = 0
	) -> None:
		self.name    = name
		self.number  = number
		self.src_loc = get_src_loc(src_loc_at)
		mapping      = OrderedDict[str, str]()

		if isinstance(io, dict):
			for (conn_pin, plat_pin) in io.items():
				if not isinstance(conn_pin, str):
					raise ToriiSyntaxError(
						f'Connector pin name must be a string, not {conn_pin!r}',
						src_loc = self.src_loc
					)
				if not isinstance(plat_pin, str):
					raise ToriiSyntaxError(
						f'Platform pin name must be a string, not {plat_pin!r}',
						src_loc = self.src_loc
					)
				mapping[conn_pin] = plat_pin

		elif isinstance(io, str):
			# NOTE(aki): once-again, mypy is being silly about redefinitions
			for (conn_pin, plat_pin) in enumerate(io.split(), start = 1): # type: ignore
				if plat_pin == '-':
					continue

				mapping[str(conn_pin)] = plat_pin
		else:
			raise ToriiSyntaxError(
				f'Connector I/Os must be a dictionary or a string, not {io!r}',
				src_loc = self.src_loc
			)

		if conn is not None:
			conn_name, conn_number = conn
			if not (isinstance(conn_name, str) and isinstance(conn_number, (int, str))):
				raise ToriiSyntaxError(
					'Connector must be None or a pair of string (connector name) and integer/string '
					f'(connector number), not {conn!r}',
					src_loc = self.src_loc
				)

			for conn_pin, plat_pin in mapping.items():
				mapping[conn_pin] = f'{conn_name}_{conn_number}:{plat_pin}'
		self.mapping = mapping

	def __repr__(self) -> str:
		return (
			f'(connector {self.name} {self.number} '
			f'{" ".join(f"{conn}=>{plat}" for conn, plat in self.mapping.items())})'
		)

	def __len__(self) -> int:
		return len(self.mapping)

	def __iter__(self) -> Generator[tuple[str, str]]:
		for conn_pin, plat_pin in self.mapping.items():
			yield f'{self.name}_{self.number}:{conn_pin}', plat_pin
