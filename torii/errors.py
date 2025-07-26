# SPDX-License-Identifier: BSD-2-Clause

'''

'''

__all__ = (
	'ToriiError',
	'ToriiWarning',

	'ToriiSyntaxError',
	'ToriiSyntaxWarning',

	'NameError',
	'NameWarning',
	'NameNotFound',

	'ToolError',
	'ToolWarning',
	'ToolNotFound',

	'DomainError',
	'DriverConflict',

	'ResourceError',
	'ResourceWarning',

	'MustUseWarning',
	'UnusedElaboratable',
	'UnusedProperty',

	'YosysError',
	'YosysWarning',
)

class ToriiError(Exception):
	''' The base class for all Torii errors '''
	pass

class ToriiWarning(Warning):
	''' The base class for all Torii warnings '''
	pass

class ToriiSyntaxError(SyntaxError):
	''' Malformed or incorrect Torii code '''
	pass

class ToriiSyntaxWarning(SyntaxWarning):
	''' Inadvisable or potentially unwanted behavior from Torii code '''
	pass

class NameError(ToriiError):
	''' Invalid HDL construct name '''
	pass

class NameWarning(ToriiWarning):
	''' Inadvisable HDL construct name '''
	pass

class NameNotFound(NameError):
	''' Unable to automatically determine name '''
	pass


class ToolError(ToriiError):
	''' An error from the execution of a tool '''
	pass

class ToolWarning(ToriiWarning):
	''' A warning from the execution of a tool '''
	pass

class ToolNotFound(ToolError):
	''' Unable to find a tool '''
	pass

class DomainError(ToriiError):
	''' A Clock Domain error '''
	pass

class DriverConflict(ToriiWarning):
	''' A Multiple-driver conflict '''
	pass

class ResourceError(ToriiError):
	''' An error with a Torii Resource '''
	pass

class ResourceWarning(ToriiWarning):
	''' A warning with a Torii Resource '''
	pass

class MustUseWarning(ToriiWarning):
	''' The base class for unused HDL objects '''
	pass

class UnusedElaboratable(MustUseWarning):
	''' A constructed, but unused/unelaborated Elaboratable '''
	# The warning is initially silenced. If everything that has been constructed remains unused,
	# it means the application likely crashed (with an exception, or in another way that does not
	# call `sys.excepthook`), and it's not necessary to show any warnings.
	# Once elaboration starts, the warning is enabled.
	_MustUse__silence = True

class UnusedProperty(MustUseWarning):
	''' A constructed, but unused Property '''
	pass

class YosysError(ToolError):
	''' An error when invoking Yosys '''
	pass

class YosysWarning(ToriiWarning):
	''' A warning emitted by Yosys '''
	pass
