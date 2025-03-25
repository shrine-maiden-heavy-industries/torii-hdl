# SPDX-License-Identifier: BSD-2-Clause

import operator
from typing import Final, SupportsIndex

__all__ = (
	'bits_for',
	'iec_size',
	'log2_ceil',
	'log2_exact',
	'ms_to_sec',
	'ns_to_sec',
	'ps_to_sec',
	'sec_to_ms',
	'sec_to_ns',
	'sec_to_ps',
	'sec_to_us',
	'us_to_sec',
)

# SI Prefix constants
EXA:   Final = 1e+18
PETA:  Final = 1e+15
TERA:  Final = 1e+12
GIGA:  Final = 1e+9
MEGA:  Final = 1e+6
KILO:  Final = 1e+3
HECTO: Final = 1e+2
DEKA:  Final = 1e+1
DECI:  Final = 1e-1
CENTI: Final = 1e-2
MILLI: Final = 1e-3
MICRO: Final = 1e-6
NANO:  Final = 1e-9
PICO:  Final = 1e-12
FEMTO: Final = 1e-15
ATTO:  Final = 1e-18

def ps_to_sec(val: float) -> float:
	'''
	Convert the given number of picoseconds into fractional seconds.

	Parameters
	----------
	val : float
		The number of picoseconds to convert into seconds.

	Example
	-------
	.. code-block:: pycon

		>>> ps_to_sec(1000000000000)
		1.0
		>>> ps_to_sec(60000000)
		6e-05

	Returns
	-------
	float
		The number of seconds.
	'''

	return val * PICO

def ns_to_sec(val: float) -> float:
	'''
	Convert the given number of nanoseconds into fractional seconds.

	Parameters
	----------
	val : float
		The number of nanoseconds to convert into seconds.

	Example
	-------
	.. code-block:: pycon

		>>> ns_to_sec(3000000000)
		3.0
		>>> ns_to_sec(5000000)
		0.005

	Returns
	-------
	float
		The number of seconds.
	'''

	return val * NANO

def us_to_sec(val: float) -> float:
	'''
	Convert the given number of microseconds into fractional seconds.

	Parameters
	----------
	val : float
		The number of microseconds to convert into seconds.

	Example
	-------
	.. code-block:: pycon

		>>> us_to_sec(1000000)
		1.0
		>>> us_to_sec(60000)
		0.06

	Returns
	-------
	float
		The number of seconds.
	'''

	return val * MICRO

def ms_to_sec(val: float) -> float:
	'''
	Convert the given number of milliseconds into fractional seconds.

	Parameters
	----------
	val : float
		The number of milliseconds to convert into seconds.

	Example
	-------
	.. code-block:: pycon

		>>> ms_to_sec(4000)
		4.0
		>>> ms_to_sec(500)
		0.5

	Returns
	-------
	float
		The number of seconds.
	'''

	return val * MILLI

def sec_to_ps(val: float) -> float:
	'''
	Convert the given number of seconds into picoseconds.

	Parameters
	----------
	val : float
		The number of seconds to convert to picoseconds.

	Example
	-------
	.. code-block:: pycon

		>>> sec_to_ps(1)
		1000000000000.0
		>>> sec_to_ps(0.00006)
		60000000.0

	Returns
	-------
	float
		The number of picoseconds.
	'''

	return val / PICO

def sec_to_ns(val: float) -> float:
	'''
	Convert the given number of seconds into nanoseconds.

	Parameters
	----------
	val : float
		The number of seconds to convert into nanoseconds.

	Example
	-------
	.. code-block:: pycon

		>>> sec_to_ns(3)
		3000000000.0
		>>> sec_to_ns(0.005)
		5000000.0

	Returns
	-------
	float
		The number of nanoseconds.
	'''

	return val / NANO

def sec_to_us(val: float) -> float:
	'''
	Convert the given number of seconds into microseconds.

	Parameters
	----------
	val : float
		The number of seconds to convert into microseconds.

	Example
	-------
	.. code-block:: pycon

		>>> sec_to_us(1)
		1000000.0
		>>> sec_to_us(0.06)
		60000.0

	Returns
	-------
	float
		The number of microseconds.
	'''

	return val / MICRO

def sec_to_ms(val: float) -> float:
	'''
	Convert the given number of seconds into milliseconds.

	Parameters
	----------
	val : float
		The number of seconds to convert into milliseconds.

	Example
	-------
	.. code-block:: pycon

		>>> sec_to_ms(4)
		4000.0
		>>> sec_to_ms(0.5)
		500.0

	Returns
	-------
	float
		The number of milliseconds.
	'''

	return val / MILLI

def iec_size(size: int, dec: int = 2) -> str:
	'''
	Converts the given number of bytes to an IEC suffixed string.

	Parameters
	----------
	size : int
		The raw byte count.
	dec : int
		The number of decimal digits to include if ``size`` is a non-whole unit.

	Example
	-------
	.. code-block:: pycon

		>>> iec_size(92873402)
		'88.57MiB'
		>>> iec_size(4294967296, 0)
		'4GiB'

	Returns
	-------
	str
		``size`` converted into the nearest IEC suffixed string possible.
	'''

	from math import floor, log, pow

	suffixes = (
		'B'  , 'KiB', 'MiB',
		'GiB', 'TiB', 'PiB',
		'EiB', 'ZiB', 'YiB',
	)

	if size == 0:
		return '0B'

	scale = int(floor(log(size, 1024)))
	power = pow(1024, scale)
	fixed = size / power
	rem = size % power

	if rem == 0 and dec == 0:
		fixed = int(fixed)
	else:
		fixed = round(fixed, dec)

	return f'{fixed}{suffixes[scale]}'

def log2_ceil(value: SupportsIndex) -> int:
	'''
	Calculate the integer result of ``⌈log₂(value)⌉``

	Parameters
	----------
	value: SupportsIndex
		The value to calculate the ``⌈log₂(value)⌉`` for.

	Example
	-------
	.. code-block:: pycon

		>>> log2_ceil(16)
		4
		>>> log2_ceil(35)
		6

	Returns
	-------
	int
		The integer log₂ of smallest power of 2 that is equal to or greater than ``value``

	Raises
	------
	ValueError
		when ``value`` is negative
	'''

	n = operator.index(value)
	if n < 0:
		raise ValueError(f'{n} is negative')
	if n == 0:
		return 0
	return (n - 1).bit_length()

def log2_exact(value: SupportsIndex) -> int:
	'''
	Calculate the integer result of ``log₂(value)`` where ``value`` is an exact power of 2.

	Parameters
	----------
	value: SupportsIndex
		The value to calculate the ``log₂(value)`` for.

	Example
	-------
	.. code-block:: pycon

		>>> log2_exact(8)
		3
		>>> log2_exact(19)
		Traceback (most recent call last):
		File "<python-input-19>", line 1, in <module>
			log2_exact(19)
			~~~~~~~~~~^^^^
		File "units.py", line 168, in log2_exact
		ValueError: 19 is not a power of 2

	Returns
	-------
	int
		The integer log₂ of ``value``

	Raises
	------
	ValueError
		when ``value`` is  not a power of 2
	'''

	n = operator.index(value)
	if n <= 0 or (n & (n - 1)):
		raise ValueError(f'{n} is not a power of 2')
	return (n - 1).bit_length()

def bits_for(value: SupportsIndex, require_sign_bit: bool = False) -> int:
	'''
	Get the number of bits needed to represent the integer value ``n``.

	Parameters
	----------
	value: SupportsIndex
		The value to find the number of bits to fit for.

	require_sign_bit: bool
		If ``value`` is signed, requiring us to add a sign bit. This is calculated automatically
		if ``value`` is less than ``0``.

	Example
	-------
	.. code-block:: pycon

		>>> bits_for(127)
		7
		>>> bits_for(127, True)
		8
		>>> bits_for(-128)
		8
		>>> bits_for(65355)
		16

	Returns
	-------
	int
		The minimum number of bits needed to represent ``n``
	'''

	n = operator.index(value)

	if n > 0:
		r = log2_ceil(n + 1)
	else:
		require_sign_bit = True
		r = log2_ceil(-n)

	if require_sign_bit:
		r += 1

	return r
