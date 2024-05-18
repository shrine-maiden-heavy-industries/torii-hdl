# SPDX-License-Identifier: BSD-2-Clause

from warnings import warn

from .lib.formal import (
	AnyConst, AnySeq, Assert, Assume, Cover, Fell, Initial,
	Past, Rose, Stable
)

warn(
	'The contents of `torii.asserts` have moved to `torii.lib.formal`',
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
