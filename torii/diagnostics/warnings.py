# SPDX-License-Identifier: BSD-2-Clause

'''

'''

__all__ = (
	'DriverConflict',
	'MustUseWarning',
	'NameWarning',
	'ResourceWarning',
	'ToolWarning',
	'ToriiSyntaxWarning',
	'ToriiWarning',
	'UnusedElaboratable',
	'UnusedProperty',
	'UnusedProperty',
	'YosysWarning',
)

class ToriiWarning(Warning):
	''' The base class for all Torii warnings '''
	pass

class ToriiSyntaxWarning(SyntaxWarning):
	''' Inadvisable or potentially unwanted behavior from Torii code '''
	msg: str
	filename: str | None
	lineno: int | None
	offset: int | None
	text: str | None
	end_lineno: int | None
	end_offset: int | None

class NameWarning(ToriiWarning):
	''' Inadvisable HDL construct name '''
	pass

class ToolWarning(ToriiWarning):
	''' A warning from the execution of a tool '''
	pass

class DriverConflict(ToriiWarning):
	''' A Multiple-driver conflict '''
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

class YosysWarning(ToriiWarning):
	''' A warning emitted by Yosys '''
	pass
