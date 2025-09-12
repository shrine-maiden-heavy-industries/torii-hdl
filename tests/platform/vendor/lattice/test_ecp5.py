# SPDX-License-Identifier: BSD-2-Clause

from unittest                           import TestCase

from torii.hdl                          import Elaboratable, Module
from torii.build.res                    import Resource, Subsignal, DiffPairs, Pins, Attrs
from torii.platform.vendor.lattice.ecp5 import ECP5Platform

class TestPlatform(ECP5Platform):
	toolchain = 'Trellis'
	device = 'LFE5UM5G-45F'
	package = 'BG381'
	speed = '8'

	resources = []
	connectors = []


class TestExtrefElaboratable(Elaboratable):
	def elaborate(self, platform: TestPlatform) -> Module:
		m = Module()
		extref0 = platform.request('extref', 0)
		return m

class TestDCUElaboratable(Elaboratable):
	def elaborate(self, platform: TestPlatform) -> Module:
		m = Module()
		dcu = platform.request('dcu', 0)
		return m

class ECP5PlatformTestCase(TestCase):
	def test_inst_dcu_good(self):
		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4', 'W5', dir = 'o')),
			Subsignal('rx', DiffPairs('Y5', 'Y6', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		platform.prepare(TestDCUElaboratable())

	def test_inst_dcu_as_pins(self) -> None:
		resource = Resource(
			'dcu', 0,
			Subsignal(
				'tx',
				Subsignal('p', Pins('W4', dir = 'o')),
				Subsignal('n', Pins('W5', dir = 'o'))
			),
			Subsignal(
				'rx',
				Subsignal('p', Pins('Y5', dir = 'i')),
				Subsignal('n', Pins('Y6', dir = 'i'))
			),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			NotImplementedError, r'^Platform \'ECP5Platform\' only supports DCU pins specified with DiffPairs$'
		):
			platform.prepare(TestDCUElaboratable())

	def test_inst_dcu_bad_diffpair(self) -> None:
		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4', 'Y6', dir = 'o')),
			Subsignal('rx', DiffPairs('Y5', 'W5', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			ValueError, r'^The DiffPairs requested \(\'W4\', \'Y6\'\) is invalid to refer to a DCU channel$'
		):
			platform.prepare(TestDCUElaboratable())

		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4', 'Y11', dir = 'o')),
			Subsignal('rx', DiffPairs('Y5', 'Y6', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			ValueError, r'^Can\'t mix EXTREF, DCU, and/or normal signals within the same subsignal\.$'
		):
			platform.prepare(TestDCUElaboratable())

	def test_inst_dcu_wrong_dir(self) -> None:
		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4', 'W5', dir = 'i')),
			Subsignal('rx', DiffPairs('Y5', 'Y6', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			ValueError, r'^DCU TX pins \(\'W4\', \'W5\'\) cannot be used as inputs$'
		):
			platform.prepare(TestDCUElaboratable())

		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4', 'W5', dir = 'o')),
			Subsignal('rx', DiffPairs('Y5', 'Y6', dir = 'o')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			ValueError, r'^DCU RX pins \(\'Y5\', \'Y6\'\) cannot be used as outputs$'
		):
			platform.prepare(TestDCUElaboratable())

	def test_inst_extref_good(self) -> None:
		resource = Resource(
			'extref', 0,
			DiffPairs('Y11', 'Y12', dir = 'i'),
			Attrs(RTERM = True, DCBIAS = True)
		)
		platform = TestPlatform()
		platform.add_resources((resource, ))

		plan = platform.prepare(TestExtrefElaboratable())

		# Grab the RTLIL generated
		rtlil = plan.files['top.il']
		assert isinstance(rtlil, str)
		# Remove the auto-gen line for Torii
		rtlil_lines = rtlil.splitlines()[1:]
		# If the line begins with `attribute` (ignoring whitespace), drop it
		rtlil_lines = list(
			filter(lambda line: not line.strip().startswith('attribute'), rtlil_lines)
		)
		# Recombobulate it and check the result is correct
		rtlil = '\n'.join(rtlil_lines)
		self.assertEqual(rtlil, r'''module \top.pin_extref_0
  wire width 1 input 0 \extref_0__p
  wire width 1 input 1 \extref_0__n
  wire width 1 \extref_0__i
  cell \EXTREFB \extref_0_0
    parameter \REFCK_DCBIAS_EN 1'1
    parameter \REFCK_RTERM 1'1
    parameter \REFCK_PWDNB 1'1
    connect \REFCLKP \extref_0__p
    connect \REFCLKN \extref_0__n
    connect \REFCLKO { \extref_0__i }
  end
end
module \top
  wire width 1 input 0 \extref_0__p
  wire width 1 input 1 \extref_0__n
  cell \top.pin_extref_0 \pin_extref_0
    connect \extref_0__p \extref_0__p
    connect \extref_0__n \extref_0__n
  end
end''') # noqa: E101

		# Grab the LPF generated
		lpf = plan.files['top.lpf']
		assert isinstance(lpf, str)
		# Remove the auto-gen line for Torii
		lpf_lines = lpf.splitlines()[1:]
		# Recombobulate it and check the result is correct
		lpf = '\n'.join(lpf_lines)
		self.assertEqual(lpf, r'''BLOCK ASYNCPATHS;
BLOCK RESETPATHS;
LOCATE COMP "extref_0__p" SITE "Y11";
LOCATE COMP "extref_0__n" SITE "Y12";
# (add_preferences placeholder)''')

	def test_inst_extref_as_pins(self) -> None:
		resource = Resource(
			'extref', 0,
			Subsignal('p', Pins('Y11', dir = 'i')),
			Subsignal('n', Pins('Y12', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			NotImplementedError, r'^The ECP5 parts do not support I/O type of single-ended input for the EXTREF blocks$'
		):
			platform.prepare(TestExtrefElaboratable())

	def test_inst_extref_bad_diffpair(self) -> None:
		resource = Resource(
			'extref', 0,
			DiffPairs('Y11', 'Y10', dir = 'i')
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			ValueError, r'^Can\'t mix EXTREF, DCU, and/or normal signals within the same subsignal\.$'
		):
			platform.prepare(TestExtrefElaboratable())

	def test_inst_extref_wrong_dir(self) -> None:
		resource = Resource(
			'extref', 0,
			DiffPairs('Y11', 'Y12', dir = 'o')
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		with self.assertRaisesRegex(
			NotImplementedError,
			r'^The ECP5 parts do not support I/O type of differential output for the EXTREF blocks$'
		):
			platform.prepare(TestExtrefElaboratable())
