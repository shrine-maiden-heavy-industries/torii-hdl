# SPDX-License-Identifier: BSD-2-Clause

'''

'''

__all__ = (
	'DomainError',
	'NameError',
	'NameNotFound',
	'ResourceError',
	'ToolError',
	'ToolNotFound',
	'ToriiError',
	'ToriiSyntaxError',
	'YosysError',
)

class ToriiError(Exception):
	''' The base class for all Torii errors '''
	pass

class ToriiSyntaxError(SyntaxError):
	''' Malformed or incorrect Torii code '''
	pass

class NameError(ToriiError):
	''' Invalid HDL construct name '''
	pass

class NameNotFound(NameError):
	''' Unable to automatically determine name '''
	pass

class ToolError(ToriiError):
	''' An error from the execution of a tool '''
	pass

class ToolNotFound(ToolError):
	''' Unable to find a tool '''
	pass

class DomainError(ToriiError):
	''' A Clock Domain error '''
	pass

class ResourceError(ToriiError):
	''' An error with a Torii Resource '''
	pass

class YosysError(ToolError):
	''' An error when invoking Yosys '''
	pass
