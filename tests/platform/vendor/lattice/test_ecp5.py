# SPDX-License-Identifier: BSD-2-Clause

from unittest                           import TestCase

from torii.hdl                          import Elaboratable, Module
from torii.build.res                    import Resource, Subsignal, DiffPairs, Pins
from torii.platform.vendor.lattice.ecp5 import ECP5Platform

class TestPlatform(ECP5Platform):
	toolchain = 'Trellis'
	device = 'LFE5UM5G-45F'
	package = 'BG381'
	speed = '8'

	resources = []
	connectors = []

class TestElaboratable(Elaboratable):
	def elaborate(self, platform: TestPlatform) -> Module:
		m = Module()
		extref0 = platform.request('extref', 0)
		return m

class ECP5PlatformTestCase(TestCase):

	def test_inst_extref_good(self):
		resource = Resource('extref', 0, DiffPairs('Y11', 'Y12', dir = 'i'))
		platform = TestPlatform()
		platform.add_resources((resource, ))

		platform.prepare(TestElaboratable())

	def test_inst_extref_as_pins(self):
		resource = Resource(
			'extref', 0,
			Subsignal('p', Pins('Y11', dir = 'i')),
			Subsignal('n', Pins('Y12', dir = 'i')),
		)
		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaises(
			NotImplementedError,
			msg = 'Platform \'ECP5Platform\' only supports EXTREF pins specified with DiffPairs'
		):
			platform.prepare(TestElaboratable())

	def test_inst_extref_bad_diffpair(self):
		resource = Resource('extref', 0, DiffPairs('Y11', 'Y10', dir = 'i'))
		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaises(
			ValueError,
			msg = 'The DiffPairs requested is invalid to refer to a EXTREF'
		):
			platform.prepare(TestElaboratable())

	def test_inst_extref_wrong_dir(self):
		resource = Resource('extref', 0, DiffPairs('Y11', 'Y12', dir = 'o'))
		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaises(
			NotImplementedError,
			msg = 'The ECP5 parts do not support I/O direction \'o\' for the EXTREF blocks'
		):
			platform.prepare(TestElaboratable())
