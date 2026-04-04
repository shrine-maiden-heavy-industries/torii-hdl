# SPDX-License-Identifier: BSD-2-Clause

'''

'''

__all__ = (
	'DomainError',
	'NameError',
	'NameNotFound',
	'NonSynthesizableError',
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
		self, *args: object, src_loc: tuple[str, int] | None = None, notes: list[str] | None = None,
		additional_ctx: tuple[str, tuple[str, int]] | None = None
	) -> None:
		if src_loc is not None:
			self.src_loc = src_loc

		if notes is not None:
			self.__notes__ = notes

		if additional_ctx is not None:
			self.additional_ctx = additional_ctx

		super().__init__(*args)

class ToriiSyntaxError(SyntaxError):
	''' Malformed or incorrect Torii code '''

	def __init__(
		self, message: str, src_loc: tuple[str, int], *, notes: list[str] | None = None,
		additional_ctx: tuple[str, tuple[str, int]] | None = None
	) -> None:
		filename, lineno = src_loc

		if notes is not None:
			self.__notes__ = notes

		if additional_ctx is not None:
			self.additional_ctx = additional_ctx

		super().__init__(message, (filename, lineno, None, None))

class NameError(ToriiError):
	''' Invalid HDL construct name '''
	pass

class NameNotFound(NameError):
	''' Unable to automatically determine name '''
	pass

class NonSynthesizableError(ToriiSyntaxError):
	''' Attempted synthesis of a non-synthesizable Torii construct '''
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
