# SPDX-License-Identifier: BSD-2-Clause

from warnings             import warn

from .lattice.machxo_2_3l import MachXO2Or3LPlatform as LatticeMachXO2Or3LPlatform
from .lattice.machxo_2_3l import MachXO2Platform     as LatticeMachXO2Platform
from .lattice.machxo_2_3l import MachXO3LPlatform    as LatticeMachXO3LPlatform


__all__ = (
	'LatticeMachXO2Or3LPlatform',
	'LatticeMachXO2Platform',
	'LatticeMachXO3LPlatform',
)

warn(
	'Instead of torii.platform.vendor.lattice_machxo_2_3l, use torii.platform.vendor.lattice.machxo_2_3l',
	DeprecationWarning, stacklevel = 2
)
