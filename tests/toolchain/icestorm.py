# SPDX-License-Identifier: BSD-2-Clause

from unittest             import TestCase


from torii_boards.lattice import icebreaker, icebreaker_bitsy, ice40_hx8k_b_evn

from .                    import _test_platform

class IcestormTestCase(TestCase):
	test_icebreaker       = _test_platform(icebreaker.ICEBreakerPlatform())
	test_icebreaker_bitsy = _test_platform(icebreaker_bitsy.ICEBreakerBitsyPlatform())
	test_ice40_hx8k_b_evn = _test_platform(ice40_hx8k_b_evn.ICE40HX8KBEVNPlatform())
