# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable
from linecache       import getlines
from re              import compile
from typing          import Union

__all__ = (
	'flatten',
	'get_linter_option',
	'get_linter_options',
	'union',
)

def flatten(i):
	for e in i:
		if isinstance(e, str) or not isinstance(e, Iterable):
			yield e
		else:
			yield from flatten(e)


def union(i, start = None):
	r = start
	for e in i:
		if r is None:
			r = e
		else:
			r |= e
	return r

def get_linter_options(filename: str) -> dict[str, Union[int, str]]:
	magic_comment = compile(r'^#\s*torii:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$')

	# Check the first five lines of the file, because it might not be first
	lines = getlines(filename)[0:5]
	if len(lines) > 0:
		matches = list(filter(lambda m: m is not None, map(magic_comment.match, lines)))

		if len(matches) > 0:
			return dict(map(lambda s: s.strip().split('=', 2), matches[0].group(1).split(',')))
	return dict()


def get_linter_option(
	filename: str , name: str, type: Union[type[bool], type[int]], default: Union[bool, int]
) -> Union[bool, int]:
	if type not in (bool, int):
		raise TypeError(f'Expected type to be either \'bool\' or \'int\', not \'{type!r}\'')

	options = get_linter_options(filename)
	if name not in options:
		return default

	option = options[name]
	if type is bool:
		if option in ('1', 'yes', 'enable'):
			return True
		if option in ('0', 'no', 'disable'):
			return False
		return default
	if type is int:
		try:
			return int(option, 0)
		except ValueError:
			return default
