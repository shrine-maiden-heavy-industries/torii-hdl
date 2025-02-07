# SPDX-License-Identifier: BSD-2-Clause

from .altera     import AlteraPlatform
from .gowin      import GowinPlatform
from .lattice    import LatticeECP5Platform, LatticeICE40Platform, LatticeMachXO2Platform, LatticeMachXO3LPlatform
from .quicklogic import QuicklogicPlatform
from .xilinx     import XilinxPlatform

__all__ = (
	'AlteraPlatform',
	'GowinPlatform',
	'LatticeECP5Platform',
	'LatticeICE40Platform',
	'LatticeMachXO2Platform',
	'LatticeMachXO3LPlatform',
	'QuicklogicPlatform',
	'XilinxPlatform',
)
