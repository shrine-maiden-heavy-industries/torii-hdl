# SPDX-License-Identifier: BSD-2-Clause

from math         import floor, log, pow
from typing       import Final, TypeVar, Generic
from warnings     import warn

from ..util.units import (
	EXA, PETA, TERA, GIGA, MEGA, KILO, HECTO, DECA, DECI, CENTI, MILLI, MICRO, NANO, PICO, FEMTO, ATTO
)

# NOTE(aki): We only export the most commonly used unit conversion operators
__all__ = (
	'Frequency',
	'GHz', 'MHz', 'kHz', 'Hz',
	'Period',
	's', 'ms', 'us', 'ns',
)

def _truncate(value: float, dig: int) -> int | float:
	'''
	Apply truncation to the given value, clamping it to ``dig`` number of trailing digits if any are present
	otherwise ``value`` is returned as an ``int`` if possible.

	Parameters
	----------
	value : float
		The value to truncate to ``dig`` if possible.

	dig : int
		The number of trailing digits to leave on ``value`` if any exist.

	Returns
	-------
	int | float
		The result of ``value`` rounded to ``dig`` if any trailing digits are found, and if none
		are present then ``value`` is returned as an ``int``
	'''

	# TODO(aki): Should we `round()` /then/ do the `.is_integer()` check?
	if value.is_integer():
		return int(value)
	return round(value, dig)

def _auto_scale(value: float, unit_scale: tuple[str, ...], dig: int) -> str:
	'''
	Automatically scale the input value to the closest whole unit and return it as a formatted string.

	Parameters
	---------
	value : float
		The value to scale.

	unit_scale : tuple[str, ...]
		The scale units in order of smallest to largest

	dig : int
		The number of trailing digits to include if any

	Returns
	-------
	str
		The formatted string of the scaled value.
	'''

	adjusted_value = (value / ATTO)

	scale = int(floor(log(adjusted_value, 1000)))
	power = pow(1000, scale)
	fixed = round(adjusted_value / power, dig)

	return f'{_truncate(fixed, dig)}{unit_scale[scale]}'

def _parse_format_spec(format_spec: str, unit_scale: tuple[str, ...]) -> tuple[str, int, bool]:
	'''
	Parse the input format specifier and return the supplied options or their defaults.

	Parameters
	----------
	format_spec : str
		The format string to parse

	unit_scale : tuple[str, ...]
		The scale units in order of smallest to largest

	Returns
	-------
	tuple[str, int, bool]
		Returns the identified scale unit, the number of trailing digits, and if the unit suffix should be stripped
		or not.
	'''

	# Split the format string on `.` to see if we are doing any trailing digit formatting
	opts = format_spec.split('.', maxsplit = 1)

	# If we have exactly 2, then assume so and set the values appropriately
	if len(opts) == 2:
		(unit, dig) = opts
		dig = int(dig, 10)
	else:
		# If not, just pull the units out and apply the default
		unit = opts[0]
		dig = 4

	# If the `unit` format specifier starts with `#` then we want to strip the unit suffix
	strip_suffix = False
	if unit.startswith('#'):
		unit = unit[1:]
		strip_suffix = True

	if unit not in ('', *unit_scale):
		raise ValueError(
			f'Unknown format specifier {unit}, expected an empty string or one of {" ".join(unit_scale)}'
		)

	return (unit, dig, strip_suffix)

class Frequency:
	'''
	Represents a frequency in whole or fractional Hertz.

	Parameters
	----------
	value: float
		The frequency in Hertz.

	Attributes
	----------
	period : torii.hdl.time.Period
		Converts this frequency into a Torii Period.

	gigahertz : float
		Returns this frequency in Gigahertz as a float literal.

	megahertz : float
		Returns this frequency in Megahertz as a float literal.

	kilohertz : float
		Returns this frequency in Kilohertz as a float literal.

	hertz : float
		Returns this frequency in Hertz as a float literal.
	'''

	_unit_scale = (
		'aHz',
		'fHz',
		'pHz',
		'nHz',
		'uHz',
		'mHz',
		'Hz',
		'kHz',
		'MHz',
		'GHz',
		'THz',
		'PHz',
		'EHz',
	)

	def __init__(self, value: float) -> None:
		self._value = value

	@property
	def period(self) -> 'Period':
		'''
		Convert this :py:class:`Frequency <torii.hdl.time.Frequency>` into a :py:class:`Period <torii.hdl.time.Period>`
		'''
		return Period(1 / self._value)

	@property
	def gigahertz(self) -> float:
		''' This frequency in Gigahertz (10^9 Hertz) '''
		return self._value / GIGA

	@property
	def megahertz(self) -> float:
		''' This frequency in Megahertz (10^6 Hertz) '''
		return self._value / MEGA

	@property
	def kilohertz(self) -> float:
		''' This frequency in Kilohertz (10^3 Hertz) '''
		return self._value / KILO

	@property
	def hertz(self) -> float:
		''' This frequency in Hertz '''
		return self._value

	def __rtruediv__(self, rep: int | float) -> 'Period':
		if rep == 1:
			warn('Consider using the `.period` attribute to get this Frequency as a Period', Warning, stacklevel = 2)
		return Period(rep / self._value)

	def __eq__(self, other: object) -> bool:
		if isinstance(other, Frequency):
			# TODO(aki): Need some reasonable Ɛ here
			return self._value == other._value
		elif isinstance(other, Period):
			return self.period == other
		else:
			return False

	def __repr__(self) -> str:
		return f'(frequency {self})'

	def __str__(self) -> str:
		return self.__format__('')

	def __format__(self, format_spec: str) -> str:
		(unit, dig, strip) = _parse_format_spec(format_spec, self._unit_scale)

		match unit:
			case 'aHz':
				return f'{_truncate(self._value / ATTO, dig)}{"" if strip else "aHz"}'
			case 'fHz':
				return f'{_truncate(self._value / FEMTO, dig)}{"" if strip else "fHz"}'
			case 'pHz':
				return f'{_truncate(self._value / PICO, dig)}{"" if strip else "pHz"}'
			case 'nHz':
				return f'{_truncate(self._value / NANO, dig)}{"" if strip else "nHz"}'
			case 'uHz':
				return f'{_truncate(self._value / MICRO, dig)}{"" if strip else "uHz"}'
			case 'mHz':
				return f'{_truncate(self._value / MILLI, dig)}{"" if strip else "mHz"}'
			case 'Hz':
				return f'{_truncate(self._value, dig)}{"" if strip else "Hz"}'
			case 'kHz':
				return f'{_truncate(self._value / KILO, dig)}{"" if strip else "kHz"}'
			case 'MHz':
				return f'{_truncate(self._value / MEGA, dig)}{"" if strip else "MHz"}'
			case 'GHz':
				return f'{_truncate(self._value / GIGA, dig)}{"" if strip else "GHz"}'
			case 'THz':
				return f'{_truncate(self._value / TERA, dig)}{"" if strip else "THz"}'
			case 'PHz':
				return f'{_truncate(self._value / PETA, dig)}{"" if strip else "PHz"}'
			case 'EHz':
				return f'{_truncate(self._value / EXA, dig)}{"" if strip else "EHz"}'
			case _:
				return _auto_scale(self._value, self._unit_scale, dig)

class Period:
	'''
	Represents a period in whole or fractional Seconds.

	Parameters
	----------
	value : float
		The period in Seconds.

	Attributes
	----------
	frequency : torii.hdl.time.Frequency
		Converts this period into a Torii Frequency.

	seconds : float
		Returns this period in Seconds as a float literal.

	milliseconds : float
		Returns this period in Milliseconds as a float literal.

	microseconds : float
		Returns this period in Microseconds as a float literal.

	nanoseconds : float
		Returns this period in Nanoseconds as a float literal.

	picoseconds : float
		Returns this period in Picoseconds as a float literal.
	'''

	_unit_scale = (
		'as',
		'fs',
		'ps',
		'ns',
		'us',
		'ms',
		's',
		'ks',
		'Ms',
		'Gs',
		'Ts',
		'Ps',
		'Es',
	)

	def __init__(self, value: float) -> None:
		self._value = value

	@property
	def frequency(self) -> 'Frequency':
		'''
		Convert this :py:class:`Period <torii.hdl.time.Period>` into a :py:class:`Frequency <torii.hdl.time.Frequency>`
		'''
		return Frequency(1 / self._value)

	@property
	def seconds(self) -> float:
		''' This period in Seconds '''
		return self._value

	@property
	def milliseconds(self) -> float:
		''' This period in Milliseconds (10^-3 Seconds) '''
		return self._value / MILLI

	@property
	def microseconds(self) -> float:
		''' This period in Microseconds (10^-6 Seconds) '''
		return self._value / MICRO

	@property
	def nanoseconds(self) -> float:
		''' This period in Nanoseconds (10^-9 Seconds) '''
		return self._value / NANO

	@property
	def picoseconds(self) -> float:
		''' This period in Picoseconds (10^-12 Seconds) '''
		return self._value / PICO

	def __rtruediv__(self, rep: int | float) -> 'Frequency':
		if rep == 1:
			warn('Consider using the `.frequency` attribute to get this Period as a Frequency', Warning, stacklevel = 2)
		return Frequency(rep / self._value)

	def __eq__(self, other: object) -> bool:
		if isinstance(other, Period):
			# TODO(aki): Need some reasonable Ɛ here
			return self._value == other._value
		elif isinstance(other, Frequency):
			return self.frequency == other
		else:
			return False

	def __repr__(self) -> str:
		return f'(period {self})'

	def __str__(self) -> str:
		return self.__format__('')

	def __format__(self, format_spec: str) -> str:
		(unit, dig, strip) = _parse_format_spec(format_spec, self._unit_scale)

		match unit:
			case 'as':
				return f'{_truncate(self._value / ATTO, dig)}{"" if strip else "as"}'
			case 'fs':
				return f'{_truncate(self._value / FEMTO, dig)}{"" if strip else "fs"}'
			case 'ps':
				return f'{_truncate(self._value / PICO, dig)}{"" if strip else "ps"}'
			case 'ns':
				return f'{_truncate(self._value / NANO, dig)}{"" if strip else "ns"}'
			case 'us':
				return f'{_truncate(self._value / MICRO, dig)}{"" if strip else "us"}'
			case 'ms':
				return f'{_truncate(self._value / MILLI, dig)}{"" if strip else "ms"}'
			case 's':
				return f'{_truncate(self._value, dig)}{"" if strip else "s"}'
			case 'ks':
				return f'{_truncate(self._value / KILO, dig)}{"" if strip else "ks"}'
			case 'Ms':
				return f'{_truncate(self._value / MEGA, dig)}{"" if strip else "Ms"}'
			case 'Gs':
				return f'{_truncate(self._value / GIGA, dig)}{"" if strip else "Gs"}'
			case 'Ts':
				return f'{_truncate(self._value / TERA, dig)}{"" if strip else "Ts"}'
			case 'Ps':
				return f'{_truncate(self._value / PETA, dig)}{"" if strip else "Ps"}'
			case 'Es':
				return f'{_truncate(self._value / EXA, dig)}{"" if strip else "Es"}'
			case _:
				return _auto_scale(self._value, self._unit_scale, dig)


_U = TypeVar('_U', bound = Frequency | Period | int | float)

class _UnitHelper(Generic[_U]):
	'''
	A helper class to allow for the use of pseudo-C++-like user-defined-literals.

	Warning
	-------
	This is an internal implementation detail for Torii, it's not recommended you
	use it for your own types as the API may change in sudden and unexpected ways.

	Example
	-------
	.. code-block:: python
		>>> Giga = _UnitHelper(1_000_000_00, int)
		>>> 5 * Giga
		5000000000
		>>> Giga(8)
		8000000000

	Parameters
	----------
	scale: int
		The scaling factor to apply to the incoming value.

	unit_type: type[_U]
		The base type.
	'''

	def __init__(self, scale: float, unit_type: type[_U]) -> None:
		self._type  = unit_type
		self._scale = scale

	def __rmul__(self, value: float | int) -> _U:
		return self._type(value * self._scale)

	def __call__(self, value: float | int) -> _U:
		return self._type(value * self._scale)

# Conversion Helpers - Frequency
EHz: Final = _UnitHelper(EXA, Frequency)
'''
Unit constant for Exahertz (10^18 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * EHz
	(frequency 1EHz)
	>>> EHz(5)
	(frequency 5EHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

PHz: Final = _UnitHelper(PETA, Frequency)
'''
Unit constant for Petahertz (10^15 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * PHz
	(frequency 1PHz)
	>>> PHz(5)
	(frequency 5PHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

THz: Final = _UnitHelper(TERA, Frequency)
'''
Unit constant for Terahertz (10^12 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * THz
	(frequency 1THz)
	>>> THz(5)
	(frequency 5THz)
'''

GHz: Final = _UnitHelper(GIGA, Frequency)
'''
Unit constant for Gigahertz (10^9 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * GHz
	(frequency 1GHz)
	>>> GHz(5)
	(frequency 5GHz)
'''

MHz: Final = _UnitHelper(MEGA, Frequency)
'''
Unit constant for Megahertz (10^6 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * MHz
	(frequency 1MHz)
	>>> MHz(5)
	(frequency 5MHz)
'''

kHz: Final = _UnitHelper(KILO, Frequency)
'''
Unit constant for Kilohertz (10^3 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * kHz
	(frequency 1kHz)
	>>> kHz(5)
	(frequency 5kHz)
'''

hHz: Final = _UnitHelper(HECTO, Frequency)
'''
Unit constant for Hectohertz (10^2).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * hHz
	(frequency 100Hz)
	>>> hHz(5)
	(frequency 500Hz)

Hint
----
For readability, consider using the standard Hertz unit.

.. code-block:: python

	>>> # Not Recommended
	>>> 1 * hHz
	(frequency 100Hz)
	>>> # Use this instead
	>>> 100 * Hz
	(frequency 100Hz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

DHz: Final = _UnitHelper(DECA, Frequency)
'''
Unit constant for Decahertz (10^1 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * DHz
	(frequency 10Hz)
	>>> DHz(5)
	(frequency 50Hz)

Hint
----
For readability, consider using the standard Hertz unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * DHz
	(frequency 10Hz)
	>>> # Use this instead
	>>> 10 * Hz
	(frequency 10Hz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

Hz: Final = _UnitHelper(1, Frequency)
'''
Unit constant for Hertz.

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * Hz
	(frequency 1Hz)
	>>> Hz(5)
	(frequency 5Hz)
'''

dHz: Final = _UnitHelper(DECI, Frequency)
'''
Unit constant for Decihertz (10^-1 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * dHz
	(frequency 10mHz)
	>>> dHz(5)
	(frequency 50mHz)

Hint
----
For readability, consider using the standard Hertz unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * dHz
	(frequency 10mHz)
	>>> # Use this instead
	>>> 0.01 * Hz
	(frequency 10mHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

cHz: Final = _UnitHelper(CENTI, Frequency)
'''
Unit constant for Centiertz (10-2 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * cHz
	(frequency 100mHz)
	>>> cHz(5)
	(frequency 500mHz)

Hint
----
For readability, consider using the standard Hertz unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * cHz
	(frequency 100mHz)
	>>> # Use this instead
	>>> 0.001 * Hz
	(frequency 100mHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

mHz: Final = _UnitHelper(MILLI, Frequency)
'''
Unit constant for Millihertz (10^-3).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * mHz
	(frequency 1mHz)
	>>> mHz(5)
	(frequency 5mHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

uHz: Final = _UnitHelper(MICRO, Frequency)
'''
Unit constant for Microhertz (10^-6).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * uHz
	(frequency 1uHz)
	>>> uHz(5)
	(frequency 5uHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

nHz: Final = _UnitHelper(NANO, Frequency)
'''
Unit constant for Nanohertz (10^-9).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * nHz
	(frequency 1nHz)
	>>> nHz(5)
	(frequency 5nHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

pHz: Final = _UnitHelper(PICO, Frequency)
'''
Unit constant for Picohertz (10^-12).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * pHz
	(frequency 1pHz)
	>>> pHz(5)
	(frequency 5pHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

fHz: Final = _UnitHelper(FEMTO, Frequency)
'''
Unit constant for Femtohertz (10^-15 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * fHz
	(frequency 1fHz)
	>>> fHz(5)
	(frequency 5fHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

aHz: Final = _UnitHelper(ATTO, Frequency)
'''
Unit constant for Attohertz (10^-18 Hertz).

See the documentation for :py:class:`Frequency <torii.hdl.time.Frequency>` for
more information on frequency units.

Example
-------
.. code-block:: pycon

	>>> 1 * aHz
	(frequency 1aHz)
	>>> aHz(5)
	(frequency 5aHz)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

# Conversion Helpers - Period

Es: Final = _UnitHelper(EXA, Period)
'''
Unit constant for Exaseconds (10^18 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * Es
	(period 1Es)
	>>> Es(5)
	(period 5Es)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

Ps: Final = _UnitHelper(PETA, Period)
'''
Unit constant for Petaseconds (10^15 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * Ps
	(period 1Ps)
	>>> Ps(5)
	(period 5Ps)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

Ts: Final = _UnitHelper(TERA, Period)
'''
Unit constant for Teraseconds (10^12 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * Ts
	(period 1Ts)
	>>> Ts(5)
	(period 5Ts)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

Gs: Final = _UnitHelper(GIGA, Period)
'''
Unit constant for Gigaseconds (10^9 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * Gs
	(period 1Gs)
	>>> Gs(5)
	(period 5Gs)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

Ms: Final = _UnitHelper(MEGA, Period)
'''
Unit constant for Megaseconds (10^6 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * Ms
	(period 1Ms)
	>>> Ms(5)
	(period 5Ms)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

ks: Final = _UnitHelper(KILO, Period)
'''
Unit constant for Kiloseconds (10^3 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * ks
	(period 1ks)
	>>> ks(5)
	(period 5ks)
'''

hs: Final = _UnitHelper(HECTO, Period)
'''
Unit constant for Hectoseconds (10^2 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * hs
	(period 100s)
	>>> hs(5)
	(period 500s)

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * hs
	(period 100s)
	>>> # Use this instead
	>>> 100 * s
	(period 100s)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

das: Final = _UnitHelper(DECA, Period)
'''
Unit constant for Decaseconds (10^1 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * das
	(period 10s)
	>>> das(5)
	(period 50s)

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * das
	(period 10s)
	>>> # Use this instead
	>>> 10 * s
	(period 10s)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

s: Final = _UnitHelper(1, Period)
'''
Unit constant for Seconds (10^0 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * s
	(period 1s)
	>>> s(5)
	(period 5s)
'''

ds: Final = _UnitHelper(DECI, Period)
'''
Unit constant for Deciseconds (10^-1 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * ds
	(period 100ms)
	>>> ds(5)
	(period 500ms)

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * ds
	(period 100ms)
	>>> # Use this instead
	>>> 0.1 * s
	(period 100ms)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

cs: Final = _UnitHelper(CENTI, Period)
'''
Unit constant for Centiseconds (10^-2 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * cs
	(period 10ms)
	>>> cs(5)
	(period 50ms)

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: pycon

	>>> # Not Recommended
	>>> 1 * cs
	(period 10ms)
	>>> # Use this instead
	>>> 0.01 * s
	(period 10ms)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''

ms: Final = _UnitHelper(MILLI, Period)
'''
Unit constant for Milliseconds (10^-3 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * ms
	(period 1ms)
	>>> ms(5)
	(period 5ms)
'''

us: Final = _UnitHelper(MICRO, Period)
'''
Unit constant for Microseconds (10^-6 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * us
	(period 1us)
	>>> us(5)
	(period 5us)
'''

ns: Final = _UnitHelper(NANO, Period)
'''
Unit constant for Nanoseconds (10^-9 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * ns
	(period 1ns)
	>>> ns(5)
	(period 5ns)
'''

ps: Final = _UnitHelper(PICO, Period)
'''
Unit constant for Picoseconds (10^-12 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * ps
	(period 1ps)
	>>> ps(5)
	(period 5ps)
'''

fs: Final = _UnitHelper(FEMTO, Period)
'''
Unit constant for Femtoseconds (10^-15 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * fs
	(period 1fs)
	>>> fs(5)
	(period 5fs)
'''

_as: Final = _UnitHelper(ATTO, Period)
'''
Unit constant for Attoseconds (10^-18 Seconds).

See the documentation for :py:class:`Period <torii.hdl.time.Period>` for
more information on period units.

Example
-------
.. code-block:: pycon

	>>> 1 * _as
	(period 1as)
	>>> _as(5)
	(period 5as)

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''
