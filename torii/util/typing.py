# SPDX-License-Identifier: PSF-2.0

# The following is a backport of the Python Typing concepts required for Torii HDL

import sys
from typing import Union, _Final, _Immutable, _GenericAlias, _type_check

def _is_param_expr(arg):
    return arg is ... or isinstance(arg,
            (tuple, list, ParamSpec, _ConcatenateGenericAlias))

def _caller(depth=1, default='__main__'):
    try:
        return sys._getframe(depth + 1).f_globals.get('__name__', default)
    except (AttributeError, ValueError):  # For platforms without _getframe()
        return None

class _ConcatenateGenericAlias(_GenericAlias, _root=True):
	def copy_with(self, params):
		if isinstance(params[-1], (list, tuple)):
			return (*params[:-1], *params[-1])
		if isinstance(params[-1], _ConcatenateGenericAlias):
			params = (*params[:-1], *params[-1].__args__)
		return super().copy_with(params)

class _PickleUsingNameMixin:
	"""Mixin enabling pickling based on self.__name__."""

	def __reduce__(self):
		return self.__name__

class _BoundVarianceMixin:
	"""Mixin giving __init__ bound and variance arguments.

	This is used by TypeVar and ParamSpec, which both employ the notions of
	a type 'bound' (restricting type arguments to be a subtype of some
	specified type) and type 'variance' (determining subtype relations between
	generic types).
	"""
	def __init__(self, bound, covariant, contravariant):
		"""Used to setup TypeVars and ParamSpec's bound, covariant and
		contravariant attributes.
		"""
		if covariant and contravariant:
			raise ValueError("Bivariant types are not supported.")
		self.__covariant__ = bool(covariant)
		self.__contravariant__ = bool(contravariant)
		if bound:
			self.__bound__ = _type_check(bound, "Bound must be a type.")
		else:
			self.__bound__ = None

	def __or__(self, right):
		return Union[self, right]

	def __ror__(self, left):
		return Union[left, self]

	def __repr__(self):
		if self.__covariant__:
			prefix = '+'
		elif self.__contravariant__:
			prefix = '-'
		else:
			prefix = '~'
		return prefix + self.__name__

class ParamSpecArgs(_Final, _Immutable, _root=True):
	"""The args for a ParamSpec object.

	Given a ParamSpec object P, P.args is an instance of ParamSpecArgs.

	ParamSpecArgs objects have a reference back to their ParamSpec:

		P.args.__origin__ is P

	This type is meant for runtime introspection and has no special meaning to
	static type checkers.
	"""
	def __init__(self, origin):
		self.__origin__ = origin

	def __repr__(self):
		return f"{self.__origin__.__name__}.args"

	def __eq__(self, other):
		if not isinstance(other, ParamSpecArgs):
			return NotImplemented
		return self.__origin__ == other.__origin__

class ParamSpecKwargs(_Final, _Immutable, _root=True):
	"""The kwargs for a ParamSpec object.

	Given a ParamSpec object P, P.kwargs is an instance of ParamSpecKwargs.

	ParamSpecKwargs objects have a reference back to their ParamSpec:

		P.kwargs.__origin__ is P

	This type is meant for runtime introspection and has no special meaning to
	static type checkers.
	"""
	def __init__(self, origin):
		self.__origin__ = origin

	def __repr__(self):
		return f"{self.__origin__.__name__}.kwargs"

	def __eq__(self, other):
		if not isinstance(other, ParamSpecKwargs):
			return NotImplemented
		return self.__origin__ == other.__origin__

class ParamSpec(_Final, _Immutable, _BoundVarianceMixin, _PickleUsingNameMixin,
				_root=True):
	"""Parameter specification variable.

	Usage::

		P = ParamSpec('P')

	Parameter specification variables exist primarily for the benefit of static
	type checkers.  They are used to forward the parameter types of one
	callable to another callable, a pattern commonly found in higher order
	functions and decorators.  They are only valid when used in ``Concatenate``,
	or as the first argument to ``Callable``, or as parameters for user-defined
	Generics.  See class Generic for more information on generic types.  An
	example for annotating a decorator::

		T = TypeVar('T')
		P = ParamSpec('P')

		def add_logging(f: Callable[P, T]) -> Callable[P, T]:
			'''A type-safe decorator to add logging to a function.'''
			def inner(*args: P.args, **kwargs: P.kwargs) -> T:
				logging.info(f'{f.__name__} was called')
				return f(*args, **kwargs)
			return inner

		@add_logging
		def add_two(x: float, y: float) -> float:
			'''Add two numbers together.'''
			return x + y

	Parameter specification variables defined with covariant=True or
	contravariant=True can be used to declare covariant or contravariant
	generic types.  These keyword arguments are valid, but their actual semantics
	are yet to be decided.  See PEP 612 for details.

	Parameter specification variables can be introspected. e.g.:

		P.__name__ == 'P'
		P.__bound__ == None
		P.__covariant__ == False
		P.__contravariant__ == False

	Note that only parameter specification variables defined in global scope can
	be pickled.
	"""

	@property
	def args(self):
		return ParamSpecArgs(self)

	@property
	def kwargs(self):
		return ParamSpecKwargs(self)

	def __init__(self, name, *, bound=None, covariant=False, contravariant=False):
		self.__name__ = name
		super().__init__(bound, covariant, contravariant)
		def_mod = _caller()
		if def_mod != 'typing':
			self.__module__ = def_mod

	def __typing_subst__(self, arg):
		if isinstance(arg, (list, tuple)):
			arg = tuple(_type_check(a, "Expected a type.") for a in arg)
		elif not _is_param_expr(arg):
			raise TypeError(f"Expected a list of types, an ellipsis, "
							f"ParamSpec, or Concatenate. Got {arg}")
		return arg

	def __typing_prepare_subst__(self, alias, args):
		params = alias.__parameters__
		i = params.index(self)
		if i >= len(args):
			raise TypeError(f"Too few arguments for {alias}")
		# Special case where Z[[int, str, bool]] == Z[int, str, bool] in PEP 612.
		if len(params) == 1 and not _is_param_expr(args[0]):
			assert i == 0
			args = (args,)
		# Convert lists to tuples to help other libraries cache the results.
		elif isinstance(args[i], list):
			args = (*args[:i], tuple(args[i]), *args[i+1:])
		return args
