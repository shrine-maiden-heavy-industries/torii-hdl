# SPDX-License-Identifier: BSD-2-Clause

from re import Match, finditer, sub

__all__ = (
	'ascii_escape',
	'tcl_escape',
	'tcl_quote',
	'tool_env_var',
)

def ascii_escape(string: str) -> str:
	''' Apply escaping to turn any character that is not A-Za-z0-9_ into hex '''

	def esc_match(m: Match) -> str:
		if m.group(1) is not None:
			return f'_{ord(m.group(1)[0]):02x}_'
		return m.group(2) # type: ignore

	return ''.join(
		map(esc_match, finditer(r'([^A-Za-z0-9_])|(.)', string))
	)

def tcl_escape(string: str) -> str:
	''' Apply appropriate escaping for use in TCL scripts '''

	return '{' + sub(r'([{}\\])', r'\\\1', string) + '}'

def tcl_quote(string: str) -> str:
	''' Apply appropriate quoting for use in TCL scripts '''

	return '"' + sub(r'([$[\\"])', r'\\\1', string) + '"'

def tool_env_var(name: str) -> str:
	'''
	Convert the given tool name into a normalized version for
	environment variables.

	This generally means replacing any `-`'s with `_`'s and any
	`+`'s with `X`'s and converting the entire name to uppercase.

	Parameters
	----------
	name : str
		The tool/executable name.

	Returns
	-------
	str
		The name of the environment variable used to look for
		for tool overrides.

	'''

	return name.upper().replace('-', '_').replace('+', 'X')
