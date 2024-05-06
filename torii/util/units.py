# SPDX-License-Identifier: BSD-2-Clause

import operator
import warnings

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
	'log2_int',
	'log2_ceil',
	'log2_exact',
)

PS = 1e-12
NS = 1e-9
US = 1e-6
MS = 1e-3

def ps_to_sec(val: float) -> float:
	''' Convert the given number of picoseconds into fractional seconds '''
	return val * PS

def ns_to_sec(val: float) -> float:
	''' Convert the given number of nanoseconds into fractional seconds '''
	return val * NS

def us_to_sec(val: float) -> float:
	''' Convert the given number of microseconds into fractional seconds '''
	return val * US

def ms_to_sec(val: float) -> float:
	''' Convert the given number of milliseconds into fractional seconds '''
	return val * MS

def sec_to_ps(val: float) -> float:
	''' Convert the give number of sections into picoseconds '''
	return val / PS

def sec_to_ns(val: float) -> float:
	''' Convert the give number of sections into nanoseconds '''
	return val / NS

def sec_to_us(val: float) -> float:
	''' Convert the give number of sections into microseconds '''
	return val / US

def sec_to_ms(val: float) -> float:
	''' Convert the give number of sections into milliseconds '''
	return val / MS

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

def log2_ceil(n):
	'''
	Returns the integer log2 of the smallest power-of-2 greater than or equal to `n`.

	Raises a `ValueError` for negative inputs.
	'''

	n = operator.index(n)
	if n < 0:
		raise ValueError(f'{n} is negative')
	if n == 0:
		return 0
	return (n - 1).bit_length()


def log2_exact(n):
	'''
	Returns the integer log2 of `n`, which must be an exact power of two.

	Raises a `ValueError` if `n` is not a power of two.
	'''

	n = operator.index(n)
	if n <= 0 or (n & (n - 1)):
		raise ValueError(f'{n} is not a power of 2')
	return (n - 1).bit_length()

def log2_int(n: int, need_pow2: bool = True) -> int:
	''' '''
	if need_pow2:
		warnings.warn(
			'`log2_int` is deprecated, replace usage of `log2_int(n, True)` with `log2_exact(n)`',
			DeprecationWarning,
			stacklevel = 2
		)
	else:
		warnings.warn(
			'`log2_int` is deprecated, replace usage of `log2_int(n, False)` with `log2_ceil(n)`',
			DeprecationWarning,
			stacklevel = 2
		)


	n = operator.index(n)
	if n == 0:
		return 0
	r = (n - 1).bit_length()
	if need_pow2 and (1 << r) != n:
		raise ValueError(f'{n} is not a power of 2')
	return r


def bits_for(n: int, require_sign_bit: bool = False) -> int:
	''' Returns the number of bits needed to represent int ``n`` '''

	n = operator.index(n)

	if n > 0:
		r = log2_ceil(n + 1)
	else:
		require_sign_bit = True
		r = log2_ceil(-n)
	if require_sign_bit:
		r += 1
	return r
