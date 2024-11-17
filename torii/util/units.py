# SPDX-License-Identifier: BSD-2-Clause

import operator
from typing import Final, SupportsIndex

__all__ = (
	'ps_to_sec',
	'ns_to_sec',
	'us_to_sec',
	'ms_to_sec',
	'sec_to_ps',
	'sec_to_ns',
	'sec_to_us',
	'sec_to_ms',
	'bits_for',
	'iec_size',
	'log2_ceil',
	'log2_exact',
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
	''' Convert the given number of picoseconds into fractional seconds '''
	return val * PICO

def ns_to_sec(val: float) -> float:
	''' Convert the given number of nanoseconds into fractional seconds '''
	return val * NANO

def us_to_sec(val: float) -> float:
	''' Convert the given number of microseconds into fractional seconds '''
	return val * MICRO

def ms_to_sec(val: float) -> float:
	''' Convert the given number of milliseconds into fractional seconds '''
	return val * MILLI

def sec_to_ps(val: float) -> float:
	''' Convert the give number of sections into picoseconds '''
	return val / PICO

def sec_to_ns(val: float) -> float:
	''' Convert the give number of sections into nanoseconds '''
	return val / NANO

def sec_to_us(val: float) -> float:
	''' Convert the give number of sections into microseconds '''
	return val / MICRO

def sec_to_ms(val: float) -> float:
	''' Convert the give number of sections into milliseconds '''
	return val / MILLI

def iec_size(size: int, dec: int = 2) -> str:
	''' Converts the given number of bytes to an IEC suffixed string '''
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
		The value to calculate the ``log₂(value)` for.

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
