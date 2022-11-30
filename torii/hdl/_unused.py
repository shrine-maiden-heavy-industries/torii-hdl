# SPDX-License-Identifier: BSD-2-Clause

from sys      import _getframe, excepthook
from types    import TracebackType
from typing   import Optional, Type
from warnings import warn_explicit

from ..util   import get_linter_option

__all__ = (
	'UnusedMustUse',
	'MustUse',
)

class UnusedMustUse(Warning):
	pass


class MustUse:
	_MustUse__silence = False
	_MustUse__warning = UnusedMustUse

	def __new__(cls, *args, src_loc_at : int = 0, **kwargs) -> 'MustUse':
		frame = _getframe(1 + src_loc_at)
		self = super().__new__(cls)
		self._MustUse__used    = False
		self._MustUse__context = dict(
			filename = frame.f_code.co_filename,
			lineno   = frame.f_lineno,
			source   = self
		)
		return self

	def __del__(self) -> None:
		if self._MustUse__silence:
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
	type : Type[BaseException], value : BaseException, traceback : Optional[TracebackType]
) -> None:
	# Don't show anything if the interpreter crashed; that'd just obscure the exception
	# traceback instead of helping.
	MustUse._MustUse__silence = True
	_old_excepthook(type, value, traceback)
excepthook = _silence_elaboratable
