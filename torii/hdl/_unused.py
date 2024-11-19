# SPDX-License-Identifier: BSD-2-Clause

from sys      import _getframe, excepthook
from types    import TracebackType
from typing   import Type, TypeVar, TypedDict, Any
from warnings import warn_explicit

from ..util   import get_linter_option

__all__ = (
	'MustUse',
	'UnusedMustUse',
)

class UnusedMustUse(Warning):
	pass

class _MustUseCtx(TypedDict):
	filename: str
	lineno: int
	source: object

T = TypeVar('T')

class MustUse:
	_MustUse__silence: bool = False
	_MustUse__warning: type[Warning] = UnusedMustUse
	_MustUse__used: bool
	_MustUse__context: _MustUseCtx

	# TODO(aki): Figure out the proper way to type this nonsense
	def __new__(cls: Type[T], *args: Any, src_loc_at: int = 0, **kwargs: Any) -> T:
		frame = _getframe(1 + src_loc_at)
		self = super().__new__(cls) # type: ignore
		self._MustUse__used    = False
		self._MustUse__context = _MustUseCtx(
			filename = frame.f_code.co_filename,
			lineno   = int(frame.f_lineno),
			source   = self
		)
		return self # type: ignore

	def __del__(self) -> None:
		if self._MustUse__silence:
			return
		if getattr(self._MustUse__warning, '_MustUse__silence', False):
			return
		if hasattr(self, '_MustUse__used') and not self._MustUse__used:
			if get_linter_option(
				self._MustUse__context['filename'],
				self._MustUse__warning.__name__, bool, True
			):
				warn_explicit(
					f'{self!r} created but never used',
					self._MustUse__warning,
					**self._MustUse__context
				)

_old_excepthook = excepthook
def _silence_elaboratable(
	type: type[BaseException], value: BaseException, traceback: TracebackType | None
) -> None:
	# Don't show anything if the interpreter crashed; that'd just obscure the exception
	# traceback instead of helping.
	MustUse._MustUse__silence = True
	_old_excepthook(type, value, traceback)
excepthook = _silence_elaboratable
