# SPDX-License-Identifier: BSD-3-Clause

from collections.abc import Callable
from functools       import wraps
from typing          import ParamSpec, TypeVar
from warnings        import warn

__all__ = (
	'deprecated',
	'final',
)

Params     = ParamSpec('Params')
ReturnType = TypeVar('ReturnType')

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
