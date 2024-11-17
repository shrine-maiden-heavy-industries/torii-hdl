# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable, Generator
from linecache       import getlines
from re              import compile, Match
from typing          import TypeAlias, TypeVar

__all__ = (
	'flatten',
	'get_linter_option',
	'get_linter_options',
	'union',
)

T = TypeVar('T')

def flatten(i: Iterable[str | T | Iterable]) -> Generator[str | T]:
	for e in i:
		if isinstance(e, str) or not isinstance(e, Iterable):
			yield e
		else:
			yield from flatten(e)

def union(i: Iterable[T], start: T | None = None) -> T:
	# NOTE(aki): The two ignores below are due to mypy having a hard time seeing through the loop/if-else
	r = start
	for e in i:
		if r is None:
			r = e
		else:
			r |= e # type: ignore
	return r # type: ignore



def get_linter_options(filename: str) -> dict[str, str]:
	magic_comment = compile(r'^#\s*torii:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$')

	# Check the first five lines of the file, because it might not be first
	lines = getlines(filename)[0:5]
	if len(lines) > 0:
		# NOTE(aki): using the lambda in `filter` is aa mypy blind-spot, ignore this
		matches: list[Match] = list(filter(lambda m: m is not None, map(magic_comment.match, lines))) # type: ignore

		if len(matches) > 0:
			return dict(map(lambda s: s.strip().split('=', 2), matches[0].group(1).split(',')))
	return dict()


LinterOptionType: TypeAlias = bool | int

def get_linter_option(
	filename: str , name: str, type: type[LinterOptionType], default: LinterOptionType
) -> LinterOptionType:
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

	return default
