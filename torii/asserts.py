# SPDX-License-Identifier: BSD-2-Clause

from warnings import warn

from .hdl.ast import (
	AnyConst, AnySeq, Assert, Assume, Cover, Fell, Initial,
	Past, Rose, Stable
)

warn(
	'The contents of `torii.asserts` have moved to `<FORMAL LIB MODULE>`',
	DeprecationWarning, stacklevel = 2
)


__all__ = (
	'AnyConst',
	'AnySeq',
	'Assert',
	'Assume',
	'Cover',
	'Fell',
	'Initial',
	'Past',
	'Rose',
	'Stable',
)
