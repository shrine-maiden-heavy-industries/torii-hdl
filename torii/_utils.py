# SPDX-License-Identifier: BSD-2-Clause

import contextlib
import functools
import warnings
import linecache
import re

from collections     import OrderedDict
from collections.abc import Iterable
from typing          import Union, Type, Dict


from .util.units     import *

__all__ = (
	'flatten',
	'union',
	'log2_int',
	'bits_for',
	'memoize',
	'final',
	'deprecated',
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


def memoize(f):
	memo = OrderedDict()

	@functools.wraps(f)
	def g(*args):
		if args not in memo:
			memo[args] = f(*args)
		return memo[args]
	return g


def final(cls):
	def init_subclass():
		raise TypeError(f'Subclassing {cls.__module__}.{cls.__name__} is not supported')
	cls.__init_subclass__ = init_subclass
	return cls


def deprecated(message : str, stacklevel : int = 2):
	def decorator(f):
		@functools.wraps(f)
		def wrapper(*args, **kwargs):
			warnings.warn(message, DeprecationWarning, stacklevel = stacklevel)
			return f(*args, **kwargs)
		return wrapper
	return decorator


def _ignore_deprecated(f = None):
	if f is None:
		@contextlib.contextmanager
		def context_like():
			with warnings.catch_warnings():
				warnings.filterwarnings(action = 'ignore', category = DeprecationWarning)
				yield
		return context_like()
	else:
		@functools.wraps(f)
		def decorator_like(*args, **kwargs):
			with warnings.catch_warnings():
				warnings.filterwarnings(action = 'ignore', category  =DeprecationWarning)
				f(*args, **kwargs)
		return decorator_like


def extend(cls):
	def decorator(f):
		if isinstance(f, property):
			name = f.fget.__name__
		else:
			name = f.__name__
		setattr(cls, name, f)
	return decorator


def get_linter_options(filename : str) -> Dict[str, Union[int, str]]:
	# Check the first five lines of the file
	magic_comments = (
		re.compile(r'^#\s*amaranth:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$'),
		re.compile(r'^#\s*torii:\s*((?:\w+=\w+\s*)(?:,\s*\w+=\w+\s*)*)\n$'),
	)

	lines = linecache.getlines(filename)[0:5]
	if len(lines) > 0:
		matches = list(filter(lambda m: m is not None, map(magic_comments[0].match, lines)))
		if len(matches) > 0:
			warnings.warn_explicit('Use `# torii:` annotation instead of `# amaranth:`',
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
