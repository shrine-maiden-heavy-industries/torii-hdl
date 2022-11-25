# SPDX-License-Identifier: BSD-2-Clause

__all__ = (
	'ns_to_sec',
	'us_to_sec',
	'ms_to_sec',
	'sec_to_ns',
	'sec_to_us',
	'sec_to_ms',
	'iec_size',
	'log2_int',
	'bits_for',
)

NS = 1e-9
US = 1e-6
MS = 1e-3

def ns_to_sec(val : float) -> float:
	''' Convert the given number of nanoseconds into fractional seconds '''
	return val * NS

def us_to_sec(val : float) -> float:
	''' Convert the given number of microseconds into fractional seconds '''
	return val * US

def ms_to_sec(val : float) -> float:
	''' Convert the given number of milliseconds into fractional seconds '''
	return val * MS

def sec_to_ns(val : float) -> float:
	''' Convert the give number of sections into nanoseconds '''
	return val / NS

def sec_to_us(val : float) -> float:
	''' Convert the give number of sections into microseconds '''
	return val / US

def sec_to_ms(val : float) -> float:
	''' Convert the give number of sections into milliseconds '''
	return val / MS

def iec_size(size : int, dec : int = 2) -> str:
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
	fixed = round((size / power), dec)

	return f'{fixed}{suffixes[scale]}'

def log2_int(n : int, need_pow2 : bool = True) -> int:
	''' '''

	if n == 0:
		return 0
	r = (n - 1).bit_length()
	if need_pow2 and (1 << r) != n:
		raise ValueError(f'{n} is not a power of 2')
	return r


def bits_for(n : int, require_sign_bit : bool = False) -> int:
	''' Returns the number of bits needed to represent int ``n`` '''

	if n > 0:
		r = log2_int(n + 1, False)
	else:
		require_sign_bit = True
		r = log2_int(-n, False)
	if require_sign_bit:
		r += 1
	return r
