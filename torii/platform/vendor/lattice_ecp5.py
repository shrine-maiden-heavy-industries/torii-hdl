# SPDX-License-Identifier: BSD-2-Clause

from warnings      import warn

from .lattice.ecp5 import ECP5Platform as LatticeECP5Platform

__all__ = (
	'LatticeECP5Platform',
)

warn(
	'Instead of torii.platform.vendor.lattice_ecp5, use torii.platform.vendor.lattice.ecp5',
	DeprecationWarning, stacklevel = 2
)
