# SPDX-License-Identifier: BSD-2-Clause
try:
	from importlib import metadata
	__version__ = metadata.version(__package__)
except ImportError: # :nocov:
	__version__ = 'unknown'

from warnings  import warn
from importlib import import_module

__all__ = (
	'Array',
	'Cat',
	'ClockDomain',
	'ClockSignal',
	'Const',
	'DomainRenamer',
	'Elaboratable',
	'EnableInserter',
	'Fragment',
	'Instance',
	'Memory',
	'Module',
	'Mux',
	'Record',
	'ResetInserter',
	'ResetSignal',
	'Shape',
	'Signal',
	'signed',
	'unsigned',
	'Value',
)

def __dir__() -> list[str]:
	return list({*globals(), *__all__, '__version__'})

def __getattr__(name: str):
	if name in __all__:
		warn(
			'Importing HDL constructs from the root Torii module is deprecated, please import from `torii.hdl` instead',
			DeprecationWarning,
			stacklevel = 2
		)
		return import_module('.hdl', __name__).__dict__[name]
	if name not in __dir__():
		raise AttributeError(f'Module {__name__!r} has not attribute {name!r}')
