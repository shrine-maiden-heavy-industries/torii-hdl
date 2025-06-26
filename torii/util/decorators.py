# SPDX-License-Identifier: BSD-3-Clause

from collections     import OrderedDict
from collections.abc import Callable
from functools       import wraps
from typing          import Any, ParamSpec, TypeVar
from warnings        import warn

__all__ = (
	'deprecated',
	'extend',
	'final',
	'memoize',
)

Params     = ParamSpec('Params')
ReturnType = TypeVar('ReturnType')

# TODO(aki): This might be replaceable with `functools.cache`?
def memoize(f: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
	memo = OrderedDict[Any, ReturnType]()

	warn(
		'torii.util.decorators.memoize has been deprecated in favor of functools.cache',
		DeprecationWarning, stacklevel = 2
	)

	@wraps(f)
	def g(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
		if args not in memo:
			memo[args] = f(*args, **kwargs)
		return memo[args]
	return g

T = TypeVar('T')

def final(cls: type[T]) -> type[T]:
	def init_subclass():
		raise TypeError(f'Subclassing {cls.__module__}.{cls.__name__} is not supported')
	# NOTE(aki): mypy says you can't assign to a method, it's wrong, you can, you just normally /shouldn't/
	cls.__init_subclass__ = init_subclass # type: ignore
	return cls

# TODO(aki): deprecate once our min python version hits 3.13
def deprecated(message: str, stacklevel: int = 2):
	def decorator(f: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
		@wraps(f)
		def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
			warn(message, DeprecationWarning, stacklevel = stacklevel)
			return f(*args, **kwargs)
		return wrapper
	return decorator

def extend(cls: type[T]):
	warn(
		'torii.util.decorators.extend has been deprecated and is slated for removal',
		DeprecationWarning, stacklevel = 2
	)

	def decorator(f: Callable[Params, ReturnType]):
		if isinstance(f, property):
			name = f.fget.__name__
		else:
			name = f.__name__
		setattr(cls, name, f)
	return decorator
