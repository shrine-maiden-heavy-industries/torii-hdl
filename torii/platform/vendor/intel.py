# SPDX-License-Identifier: BSD-2-Clause

from warnings import warn

from .altera import AlteraPlatform

warn(
	'The `IntelPlatform` has been renamed to `AlteraPlatform`',
	DeprecationWarning, stacklevel = 2
)


__all__ = (
	'IntelPlatform'
)

IntelPlatform = AlteraPlatform
