# SPDX-License-Identifier: BSD-2-Clause

from warnings  import warn
from importlib import import_module

__all__ = ( # noqa: F822
	'Arbiter',
	'BurstTypeExt',
	'CycleType',
	'Decoder',
	'Interface',
)

def __dir__() -> list[str]:
	return list({*globals(), *__all__})

def __getattr__(name: str):
	if name in __all__:
		warn(
			'The `torii.lib.soc.wishbone.bus` module has moved to `torii.lib.bus.wishbone` and has been deprecated',
			DeprecationWarning,
			stacklevel = 2
		)
		return import_module('torii.lib.bus.wishbone').__dict__[name]
	if name not in __dir__():
		raise AttributeError(f'Module {__name__!r} has not attribute {name!r}')
