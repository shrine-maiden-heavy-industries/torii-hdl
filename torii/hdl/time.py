# SPDX-License-Identifier: BSD-2-Clause

'''

'''

from typing       import Final, TypeVar, Generic

from ..util.units import (
	EXA, PETA, TERA, GIGA, MEGA, KILO, HECTO, DECA, DECI, CENTI, MILLI, MICRO, NANO, PICO, FEMTO, ATTO
)

# NOTE(aki): We only export the most commonly used unit conversion operators
__all__ = (
	'Frequency',
	'GHz', 'MHz', 'kHz', 'Hz',
	'Period',
	'ks', 's', 'ms', 'us', 'ns', 'ps', 'fs',
)


class Frequency:
	'''
	Represents a frequency in whole or fractional Hertz.


	Parameters
	----------
	value: int
		The frequency value
	'''

	def __init__(self, value: int) -> None:
		self._value = value

	def period(self) -> 'Period':
		''' Convert this :py:class:`Frequency` into a :py:class:`Period` '''

		return Period(self._value)

	@property
	def gigahertz(self) -> float:
		''' This frequency in Gigahertz '''

		return self._value / GIGA

	@property
	def megahertz(self) -> float:
		''' This frequency in Megahertz '''

		return self._value / MEGA

	@property
	def kilohertz(self) -> float:
		''' This frequency in Kilohertz '''

		return self._value / KILO

	@property
	def hertz(self) -> float:
		''' This frequency in Hertz '''

		return self._value

	def __repr__(self) -> str:
		return f'<Frequency: {self}>'

	def __str__(self) -> str:
		return self.__format__('')

	def __format__(self, format_spec: str) -> str:
		return ''

class Period:
	'''

	'''

	def __init__(self, value: int) -> None:
		self._value = value

	def frequency(self) -> 'Frequency':
		''' Convert this :py:class:`Period` into a :py:class:`Frequency` '''

		return Frequency(self._value)

	@property
	def seconds(self) -> float:
		''' This period in Seconds '''

		return self._value

	@property
	def milliseconds(self) -> float:
		''' This period in Milliseconds '''

		return self._value / MILLI

	@property
	def microseconds(self) -> float:
		''' This period in Microeconds '''

		return self._value / MICRO

	@property
	def nanoseconds(self) -> float:
		''' This period in Nanoeconds '''

		return self._value / NANO

	@property
	def picoseconds(self) -> float:
		''' This period in Picoseconds '''

		return self._value / PICO

	@property
	def femtoseconds(self) -> float:
		''' This period in Femtoseconds '''

		return self._value

	def __repr__(self) -> str:
		return f'<Period: {self}>'

	def __str__(self) -> str:
		return self.__format__('')

	def __format__(self, format_spec: str) -> str:
		return ''

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
	.. code-block:: pycon

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

	def __init__(self, scale: int, unit_type: type[_U]) -> None:
		self._type  = unit_type
		self._scale = scale

	def __mul__(self, value: float | int) -> _U:
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
	<Frequency: 1e+18 Hertz>
	>>> EHz(5)
	<Frequency: 5e+18 Hertz>

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
	<Frequency: 1e+15 Hertz>
	>>> PHz(5)
	<Frequency: 5e+15 Hertz>

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
	<Frequency: 1e+12 Hertz>
	>>> THz(5)
	<Frequency: 5e+12 Hertz>
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
	<Frequency: 1e+9 Hertz>
	>>> GHz(5)
	<Frequency: 5e+9 Hertz>
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
	<Frequency: 1e+6 Hertz>
	>>> MHz(5)
	<Frequency: 5e+6 Hertz>
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
	<Frequency: 1e+3 Hertz>
	>>> kHz(5)
	<Frequency: 5e+3 Hertz>
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
	<Frequency: 1e+2 Hertz>
	>>> hHz(5)
	<Frequency: 5e+2 Hertz>

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
	<Frequency: 1e+1 Hertz>
	>>> DHz(5)
	<Frequency: 5e+1 Hertz>

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
	<Frequency: 1 Hertz>
	>>> Hz(5)
	<Frequency: 5 Hertz>
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
	<Frequency: 1e-1 Hertz>
	>>> dHz(5)
	<Frequency: 5e-1 Hertz>

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
	<Frequency: 1e-2 Hertz>
	>>> cHz(5)
	<Frequency: 1e-2 Hertz>

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
	<Frequency: 1e-3 Hertz>
	>>> mHz(5)
	<Frequency: 5e-3 Hertz>

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
	<Frequency: 1e-6 Hertz>
	>>> uHz(5)
	<Frequency: 5e-6 Hertz>

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
	<Frequency: 1e-9 Hertz>
	>>> nHz(5)
	<Frequency: 5e-9 Hertz>

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
	<Frequency: 1e-12 Hertz>
	>>> pHz(5)
	<Frequency: 5e-12 Hertz>

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
	<Frequency: 1e-15 Hertz>
	>>> fHz(5)
	<Frequency: 5e-15 Hertz>

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
	<Frequency: 1e-18 Hertz>
	>>> aHz(5)
	<Frequency: 5e-18 Hertz>

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
	<Period: 1e+18 Seconds>
	>>> Es(5)
	<Period: 5e+18 Seconds>

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
	<Period: 1e+15 Seconds>
	>>> Ps(5)
	<Period: 5e+15 Seconds>

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
	<Period: 1e+12 Seconds>
	>>> Ts(5)
	<Period: 5e+12 Seconds>

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
	<Period: 1e+9 Seconds>
	>>> Gs(5)
	<Period: 5e+9 Seconds>

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
	<Period: 1e+6 Seconds>
	>>> Ms(5)
	<Period: 5e+6 Seconds>

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
	<Period: 1e+3 Seconds>
	>>> ks(5)
	<Period: 5e+3 Seconds>
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
	<Period: 1e+2 Seconds>
	>>> hs(5)
	<Period: 5e+2 Seconds>

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: python

	# Not Recommended
	1 * hs
	# Use this instead
	100 * s

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
	<Period: 1e+1 Seconds>
	>>> das(5)
	<Period: 5e+1 Seconds>

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: python

	# Not Recommended
	1 * das
	# Use this instead
	10 * s

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
	<Period: 1e+0 Seconds>
	>>> s(5)
	<Period: 5e+0 Seconds>
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
	<Period: 1e-1 Seconds>
	>>> ds(5)
	<Period: 5e-1 Seconds>

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: python

	# Not Recommended
	1 * ds
	# Use this instead
	0.1 * s

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
	<Period: 1e-2 Seconds>
	>>> cs(5)
	<Period: 5e-2 Seconds>

Hint
----
For readability, consider using the standard Second unit.

.. code-block:: python

	# Not Recommended
	1 * cs
	# Use this instead
	0.01 * s

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
	<Period: 1e-3 Seconds>
	>>> ms(5)
	<Period: 5e-3 Seconds>
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
	<Period: 1e-6 Seconds>
	>>> us(5)
	<Period: 5e-6 Seconds>
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
	<Period: 1e-9 Seconds>
	>>> ns(5)
	<Period: 5e-9 Seconds>
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
	<Period: 1e-12 Seconds>
	>>> ps(5)
	<Period: 5e-12 Seconds>
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
	<Period: 1e-15 Seconds>
	>>> fs(5)
	<Period: 5e-15 Seconds>
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
	<Period: 1e-18 Seconds>
	>>> _as(5)
	<Period: 5e-18 Seconds>

Warning
-------
This is a very uncommon unit, if you're using this you should double check why.
'''
