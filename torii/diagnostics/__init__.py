# SPDX-License-Identifier: BSD-2-Clause

from .errors   import (
	AttributeError, ConstraintError, DomainError, DriverConflictError, ElaborationError, IndexError, NameError,
	NameNotFound, NonSynthesizableError, PlatformError, ResourceError, ToolError, ToolNotFound, ToriiError,
	ToriiSyntaxError, YosysError,
)
from .warnings import (
	ConstraintWarning, DriverConflictWarning, ElaborationWarning, MustUseWarning, NameWarning, PlatformWarning,
	ResourceWarning, ToolWarning, ToriiSyntaxWarning, ToriiWarning, UnusedElaboratable, UnusedProperty, YosysWarning,
)

__all__ = (
	'AttributeError',
	'ConstraintError',
	'ConstraintWarning',
	'DomainError',
	'DriverConflictError',
	'DriverConflictWarning',
	'ElaborationError',
	'ElaborationWarning',
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
