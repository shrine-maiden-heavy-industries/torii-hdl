# SPDX-License-Identifier: BSD-2-Clause

from .ecp5        import ECP5Platform        as LatticeECP5Platform
from .ice40       import ICE40Platform       as LatticeICE40Platform
from .machxo_2_3l import MachXO2Or3LPlatform as LatticeMachXO2Or3LPlatform
from .machxo_2_3l import MachXO2Platform     as LatticeMachXO2Platform
from .machxo_2_3l import MachXO3LPlatform    as LatticeMachXO3LPlatform


__all__ = (
	'LatticeECP5Platform',
	'LatticeICE40Platform',
	'LatticeMachXO2Or3LPlatform',
	'LatticeMachXO2Platform',
	'LatticeMachXO3LPlatform',
)
