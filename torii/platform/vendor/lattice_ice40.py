# SPDX-License-Identifier: BSD-2-Clause

from warnings       import warn

from .lattice.ice40 import ICE40Platform as LatticeICE40Platform

__all__ = (
	'LatticeICE40Platform',
)

warn(
	'Instead of torii.platform.vendor.lattice_ice40, use torii.platform.vendor.lattice.ice40',
	DeprecationWarning, stacklevel = 2
)
