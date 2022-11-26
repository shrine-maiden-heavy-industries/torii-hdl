# SPDX-License-Identifier: BSD-2-Clause

from .intel               import IntelPlatform
from .lattice_ecp5        import LatticeECP5Platform
from .lattice_ice40       import LatticeICE40Platform
from .lattice_machxo_2_3l import LatticeMachXO2Platform, LatticeMachXO3LPlatform
from .quicklogic          import QuicklogicPlatform
from .xilinx              import XilinxPlatform

__all__ = (
	'IntelPlatform',

	'LatticeECP5Platform',
	'LatticeICE40Platform',
	'LatticeMachXO2Platform',
	'LatticeMachXO3LPlatform',

	'QuicklogicPlatform',

	'XilinxPlatform',
)
