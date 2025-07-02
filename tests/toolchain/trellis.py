# SPDX-License-Identifier: BSD-2-Clause

from unittest             import TestCase

# ECP5
from torii_boards.lattice import versa_ecp5, versa_ecp5_5g

from .                    import _test_platform

# TODO(aki): Other supported Trellis platforms

class TrellisECP5TestCase(TestCase):
	test_versa_ecp5   = _test_platform(versa_ecp5.VersaECP5Platform())
	test_versa_ecp55g = _test_platform(versa_ecp5_5g.VersaECP55GPlatform())
