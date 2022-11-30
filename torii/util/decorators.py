# SPDX-License-Identifier: BSD-3-Clause


from collections import OrderedDict
from functools   import wraps
from warnings    import warn

__all__ = (
	'memoize',
	'final',
	'deprecated',
	'extend'
)

def memoize(f):
	memo = OrderedDict()

	@wraps(f)
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
		@wraps(f)
		def wrapper(*args, **kwargs):
			warn(message, DeprecationWarning, stacklevel = stacklevel)
			return f(*args, **kwargs)
		return wrapper
	return decorator

def extend(cls):
	def decorator(f):
		if isinstance(f, property):
			name = f.fget.__name__
		else:
			name = f.__name__
		setattr(cls, name, f)
	return decorator
