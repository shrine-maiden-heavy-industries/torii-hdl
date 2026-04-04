# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable
from re              import Match, finditer, sub

__all__ = (
	'ascii_escape',
	'tcl_escape',
	'tcl_quote',
	'tool_env_var',
)

def ascii_escape(string: str) -> str:
	'''
	Apply escaping to turn any character that is not ``A-Za-z0-9_`` into hex.

	Parameters
	----------
	string: str
		The string to escape.

	Example
	-------
	.. code-block:: pycon

		>>> ascii_escape('Hello ニャ~!')
		'Hello_20__30cb__30e3__7e__21_'

	Returns
	-------
	str
		The string with any applicable characters escaped appropriately.
	'''

	def esc_match(m: Match) -> str:
		if m.group(1) is not None:
			return f'_{ord(m.group(1)[0]):02x}_'
		return m.group(2) # type: ignore

	return ''.join(
		map(esc_match, finditer(r'([^A-Za-z0-9_])|(.)', string))
	)

def tcl_escape(string: str) -> str:
	'''
	Apply appropriate escaping for use in TCL scripts.

	Parameters
	----------
	string: str
		The string to escape.

	Example
	-------
	.. code-block:: pycon

		>>> tcl_escape('nya {nya} [nya] \\nya')
		'{nya \\{nya\\} [nya] \\\\nya}'

	Returns
	-------
	str
		The string with any applicable characters escaped appropriately.
	'''

	return '{' + sub(r'([{}\\])', r'\\\1', string) + '}'

def tcl_quote(string: str) -> str:
	'''
	Apply appropriate quoting for use in TCL scripts.

	Parameters
	----------
	string: str
		The string to escape.

	Example
	-------
	.. code-block:: pycon

		>>> tcl_quote('Meow "meow"')
		'"Meow \\"meow\\""'
		>>> tcl_quote("Meow 'meow'")
		'"Meow \'meow\'"'

	Returns
	-------
	str
		The string with any applicable characters escaped appropriately.
	'''

	return '"' + sub(r'([$[\\"])', r'\\\1', string) + '"'

def tool_env_var(name: str) -> str:
	'''
	Convert the given tool name into a normalized version for
	environment variables.

	This generally means replacing any ``-``'s with ``_``'s and any
	``+``'s with ``X``'s and converting the entire name to uppercase.

	Parameters
	----------
	name: str
		The tool/executable name.

	Example
	-------
	.. code-block:: pycon

		>>> tool_env_var('cat')
		'CAT'
		>>> tool_env_var('cat-girl')
		'CAT_GIRL'

	Returns
	-------
	str
		The name of the environment variable used to look for
		for tool overrides.
	'''

	return name.upper().replace('-', '_').replace('+', 'X')

def _get_best_matching(input: str, candidates: Iterable[str]) -> list[str]:
	'''
	Compute the Damerau-Levenshtein of the given input over the collection of
	possible candidates and return the 4 most likely matches.

	Parameters
	----------
	input: str
		The string we are comparing our possible matches against

	candidates: Iterable[str]
		The collection of candidate strings we want to check against

	Returns
	-------
	list[str]
		A sorted list of strings in order of best matching
	'''

	ranked = filter(lambda item: item[0] < 6, sorted({
		_damerau_levenshtein(input, item): item for item in candidates
	}.items()))

	return list(map(lambda item: item[1], ranked))[:4]

def _damerau_levenshtein(
	input: str, target: str, addition: int = 1, deletion: int = 3, substitution: int = 2, transposition: int = 0
) -> int:
	'''
	Compute the weighted Damerau-Levenshtein between the input and the target.

	Parameters
	----------
	input: str
		The provided input to compare.

	target: str
		The target we are comparing the input against.

	addition: int
		How heavily to weigh character additions/insertions.

	deletion: int
		How heavily to weigh character deletions/removals.

	substitution: int
		How heavily to weigh character substitutions.

	transposition: int
		How heavily to weigh character transpositions.

	Returns
	-------
	int
		The number of total edits needed to turn the input into the target
	'''

	target_len = len(target)
	input_len = len(input)

	row0 = [0] * (input_len + 1)
	row1 = [0] * (input_len + 1)
	row2 = [0] * (input_len + 1)

	for j in range(0, input_len):
		row1[j] = j * addition

	for i in range(0, target_len):
		row2[0] = (i + 1) * deletion
		for j in range(0, input_len):
			row2[j + 1] = row1[j] + substitution * (target[i] != input[j])

			# If the two adjacent characters in target/input are transposed
			is_transposed = target[i - 1] == input[j] and target[i] == input[j - 1]
			# The transposition weight
			trans = row0[j - 1] + transposition
			# The deletion weight
			delete = row1[j + 1] + deletion
			# The addition weight
			add = row2[j] + addition

			if i > 0 and j > 0 and is_transposed and row2[j + 1] > trans:
				row2[j + 1] = trans

			if row2[j + 1] > delete:
				row2[j + 1] = delete

			if row2[j + 1] > add:
				row2[j + 1] = add

		temp = row0
		row0 = row1
		row1 = row2
		row2 = temp

	return row1[input_len]
