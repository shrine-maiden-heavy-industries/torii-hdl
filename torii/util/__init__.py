# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable
from linecache       import getlines
from re              import compile
from typing          import Dict, Type, Union
from warnings        import warn_explicit

__all__ = (
	'flatten',
	'union',
	'get_linter_options',
	'get_linter_option',
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

def get_linter_options(filename : str) -> Dict[str, Union[int, str]]:
	# Check the first five lines of the file
	magic_comments = (
		compile(r'^#\s*amaranth:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$'),
		compile(r'^#\s*torii:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$'),
	)

	lines = getlines(filename)[0:5]
	if len(lines) > 0:
		matches = list(filter(lambda m: m is not None, map(magic_comments[0].match, lines)))
		if len(matches) > 0:
			warn_explicit('Use `# torii:` annotation instead of `# amaranth:`',
				DeprecationWarning, filename, 1)
		else:
			matches = list(filter(lambda m: m is not None, map(magic_comments[1].match, lines)))

		if len(matches) > 0:
			return dict(map(lambda s: s.strip().split('=', 2), matches[0].group(1).split(',')))
	return dict()


def get_linter_option(
	filename : str , name : str, type : Union[Type[bool], Type[int]], default : Union[bool, int]
) -> Union[bool, int]:
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
	assert False
