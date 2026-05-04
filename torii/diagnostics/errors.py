# SPDX-License-Identifier: BSD-2-Clause

from .._typing import SrcLoc

'''

'''

__all__ = (
	'AttributeError',
	'ConstraintError',
	'DomainError',
	'DriverConflictError',
	'IndexError',
	'NameError',
	'NameNotFound',
	'NonSynthesizableError',
	'PlatformError',
	'ResourceError',
	'ToolError',
	'ToolNotFound',
	'ToriiError',
	'ToriiSyntaxError',
	'YosysError',
)

class ToriiError(Exception):
	''' The base class for all Torii errors '''

	def __init__(
		self, *args: object, message: str | None = None, src_loc: SrcLoc | None = None,
		notes: list[str] | None = None, additional_ctx: tuple[str, SrcLoc] | None = None
	) -> None:
		self.msg = message

		if src_loc is None:
			filename = None
			lineno = None
		else:
			filename, lineno = src_loc

		self.filename = filename
		self.lineno = lineno

		if notes is not None:
			self.__notes__ = notes

		if additional_ctx is not None:
			self.additional_ctx = additional_ctx

		if len(args) == 0 and message is not None:
			super().__init__(message)
		else:
			super().__init__(*args)

class ToriiSyntaxError(SyntaxError):
	''' Malformed or incorrect Torii code '''

	def __init__(
		self, message: str, src_loc: SrcLoc | None, *, notes: list[str] | None = None,
		additional_ctx: tuple[str, SrcLoc] | None = None
	) -> None:
		if src_loc is None:
			filename = None
			lineno = None
		else:
			filename, lineno = src_loc

		if notes is not None:
			self.__notes__ = notes

		if additional_ctx is not None:
			self.additional_ctx = additional_ctx

		super().__init__(message, (filename, lineno, None, None))

class ConstraintError(ToriiError):
	''' An invalid constraint '''
	pass

class NameError(ToriiError):
	''' Invalid HDL construct name '''
	pass

class NameNotFound(NameError):
	''' Unable to automatically determine name '''
	pass

class NonSynthesizableError(ToriiSyntaxError):
	''' Attempted synthesis of a non-synthesizable Torii construct '''
	pass

class PlatformError(ToriiError):
	''' An error relating to some functionality of a Torii platform '''
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

class IndexError(ToriiSyntaxError, IndexError):
	'''  '''
	pass

class AttributeError(ToriiError, AttributeError):
	'''
	A hybrid between the Python :py:class:`AttributeError` and :py:class:`ToriiError`.

	This is used for where we wish to maintain proper functionality with things such as the
	python :py:meth:`hasattr` call, but also if not caught emit a pretty Torii diagnostic
	'''
	pass

class DriverConflictError(ToriiError):
	''' A driver-driver conflict '''
	pass
