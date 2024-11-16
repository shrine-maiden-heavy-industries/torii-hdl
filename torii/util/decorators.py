# SPDX-License-Identifier: BSD-3-Clause


from collections     import OrderedDict
from collections.abc import Callable
from typing          import ParamSpec, TypeVar, Any
from functools       import wraps
from warnings        import warn

__all__ = (
	'deprecated',
	'extend',
	'final',
	'memoize',
)

Params     = ParamSpec('Params')
ReturnType = TypeVar('ReturnType')

def memoize(f: Callable[Params, ReturnType]):
	memo = OrderedDict[Any, ReturnType]()

	@wraps(f)
	def g(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
		if args not in memo:
			memo[args] = f(*args, **kwargs)
		return memo[args]
	return g

def final(cls):
	def init_subclass():
		raise TypeError(f'Subclassing {cls.__module__}.{cls.__name__} is not supported')
	cls.__init_subclass__ = init_subclass
	return cls

def deprecated(message: str, stacklevel: int = 2):
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
