# SPDX-License-Identifier: BSD-2-Clause

__all__ = (
	'log2_int',
	'bits_for',
)

def log2_int(n : int, need_pow2 : bool = True) -> int:
	if n == 0:
		return 0
	r = (n - 1).bit_length()
	if need_pow2 and (1 << r) != n:
		raise ValueError(f'{n} is not a power of 2')
	return r


def bits_for(n : int, require_sign_bit : bool = False) -> int:
	if n > 0:
		r = log2_int(n + 1, False)
	else:
		require_sign_bit = True
		r = log2_int(-n, False)
	if require_sign_bit:
		r += 1
	return r
