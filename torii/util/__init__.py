# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Generator, Iterable
from functools       import cache
from linecache       import getlines
from operator        import ior
from re              import Match, compile
from typing          import TypeAlias, TypeVar

__all__ = (
	'flatten',
	'get_linter_option',
	'get_linter_options',
	'union',
)

T = TypeVar('T')

# NOTE(aki): The explicit `str` in the type is to make type checking happy
def flatten(iter: Iterable[str | T | Iterable]) -> Generator[str | T]:
	'''
	Flatten nested iterables into a single iterator.

	Parameters
	----------
	iter : Iterable[str | T | Iterable]
		The nested iterator to flatten

	Returns
	-------
	Generator[str | T]
		The flattened sequence.
	'''

	for element in iter:
		if isinstance(element, str) or not isinstance(element, Iterable):
			yield element
		else:
			yield from flatten(element)


def union(iter: Iterable[T], start: T | None = None) -> T:
	'''
	Apply :py:meth:`operator.ior` over the iterable ``iter``.

	Unlike :py:meth:`functools.accumulate`, this method only returns the final result, and not
	all the intermediate steps.

	Parameters
	----------
	iter : Iterable[T]
		The iterable to apply :py:meth:`operator.ior` over.

	start : T | None
		The initial value for the result of the union.

	Returns
	-------
	T
		The result of the union operation.

	'''

	# NOTE(aki): The two ignores below are due `operator.ior` being stupid and using `Any` for typing rather than a typevar
	result = start
	for element in iter:
		if result is None:
			result = element
		else:
			result = ior(result, element) # type: ignore
	return result # type: ignore

@cache
def get_linter_options(filename: str) -> dict[str, str]:
	'''
	Read the given Python source file given by ``filename`` and extract any "Magic Comments" that Torii knows how to parse
	and return them as a key-value set of options.

	The "Magic Comments" look as follows:

	.. code-block:: python

		# torii: NAME=VALUE
		# torii: NAME=VALUE, NAME2=VALUE2

	The general format is the string ``# torii:`` followed by one or more ``NAME=VALUE`` pairs separated by commas. ``NAME`` and
	``VALUE`` are one or more alphanumeric characters.

	Parameters
	----------
	filename : str
		The name of the Python source file to ingest

	Returns
	-------
	dict[str, str]
		All of the found settings from the given file.
	''' # noqa: E501

	magic_comment = compile(r'^#\s*torii:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)$')

	lines = getlines(filename)
	if len(lines) > 0:
		matches: list[Match] = [
			match for match in (
				magic_comment.match(line)
				for line in lines
				if line.startswith('#')
			) if match is not None
		]

		if len(matches) > 0:
			opts: dict[str, str] = {
				key: value for (key, value) in (
					opt.strip().split('=', 2) for opt in flatten(
						match.group(1).split(',') for match in matches
					)
				)
			}

			return opts

	return dict()

LinterOptionType: TypeAlias = bool | int

@cache
def get_linter_option(
	filename: str , name: str, type: type[LinterOptionType], default: LinterOptionType
) -> LinterOptionType:
	'''
	Read the Python source file from the given file ``filename`` and search for the option by the name of ``name``
	in the "Magic Comments" in the file.

	The value of ``name`` is parsed according to rules set out by ``type``, and if ``name`` is not found, then the value
	of ``default`` is returned instead.

	See :py:meth:`get_linter_options` for more information on the "Magic Comment" format.

	Currently the following option types are supported:

	* :py:class:`bool` - The values of ``0``, ``off``, ``no``, ``disable``, and ``disabled`` are ``False`` while ``1``, ``on``, ``yes``, ``enable``, and ``enabled`` are ``True``
	* :py:class:`int` - Any valid number that can be parsed from ``int(value, 0)``.

	Parameters
	----------
	filename : str
		The name of the Python source file to ingest.

	name : str
		The name of the option to get.

	type : type[LinterOptionType]
		The type of the option ``name``.

	default : LinterOptionType
		The default value to return if ``name`` is not found.

	Returns
	-------
	LinterOptionType
		The value of the option ``name`` if found or ``default`` if it's not

	Raises
	------
	TypeError
		If ``type`` is not a valid option type.

	''' # noqa: E501

	if type not in (bool, int):
		raise TypeError(f'Expected type to be either \'bool\' or \'int\', not {type!r}')

	options = get_linter_options(filename)
	if name not in options:
		return default

	option = options[name]
	if type is bool:
		if option in ('1', 'on', 'yes', 'enable', 'enabled'):
			return True
		if option in ('0', 'off', 'no', 'disable', 'disabled'):
			return False
		return default
	if type is int:
		try:
			return int(option, 0)
		except ValueError:
			return default

	return default
