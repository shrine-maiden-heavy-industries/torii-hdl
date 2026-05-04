# SPDX-License-Identifier: BSD-2-Clause

from .errors   import (
	AttributeError, ConstraintError, DomainError, DriverConflictError, IndexError, NameError, NameNotFound,
	NonSynthesizableError, PlatformError, ResourceError, ToolError, ToolNotFound, ToriiError, ToriiSyntaxError,
	YosysError,
)
from .warnings import (
	ConstraintWarning, DriverConflict, MustUseWarning, NameWarning, PlatformWarning, ResourceWarning, ToolWarning,
	ToriiSyntaxWarning, ToriiWarning, UnusedElaboratable, UnusedProperty, YosysWarning,
)

__all__ = (
	'AttributeError',
	'ConstraintError',
	'ConstraintWarning',
	'DomainError',
	'DriverConflict',
	'DriverConflictError',
	'IndexError',
	'MustUseWarning',
	'NameError',
	'NameNotFound',
	'NameWarning',
	'NonSynthesizableError',
	'PlatformError',
	'PlatformWarning',
	'ResourceError',
	'ResourceWarning',
	'ToolError',
	'ToolNotFound',
	'ToolWarning',
	'ToriiError',
	'ToriiSyntaxError',
	'ToriiSyntaxWarning',
	'ToriiWarning',
	'UnusedElaboratable',
	'UnusedProperty',
	'YosysError',
	'YosysWarning',
)
