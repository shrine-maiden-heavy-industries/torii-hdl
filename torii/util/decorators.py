# SPDX-License-Identifier: BSD-3-Clause


from collections import OrderedDict
from contextlib  import contextmanager
from functools   import wraps
from warnings    import catch_warnings, filterwarnings, warn

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


def _ignore_deprecated(f = None):
	if f is None:
		@contextmanager
		def context_like():
			with catch_warnings():
				filterwarnings(action = 'ignore', category = DeprecationWarning)
				yield
		return context_like()
	else:
		@wraps(f)
		def decorator_like(*args, **kwargs):
			with catch_warnings():
				filterwarnings(action = 'ignore', category  =DeprecationWarning)
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
