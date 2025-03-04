# SPDX-License-Identifier: BSD-2-Clause
try:
	from importlib import metadata
	__version__ = metadata.version(__package__)
except ImportError: # :nocov:
	__version__ = 'unknown'

from .hdl import (
	Array, Cat, ClockDomain, ClockSignal, Const, DomainRenamer,
	Elaboratable, EnableInserter, Fragment, Instance, Memory,
	Module, Mux, Record, ResetInserter, ResetSignal, Shape,
	Signal, Value, signed, unsigned
)

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
