# SPDX-License-Identifier: BSD-2-Clause

from typing import Literal
from unittest                           import TestCase

from torii.hdl                          import Instance, Elaboratable, Module
from torii.build.res                    import Resource, Subsignal, DiffPairs, Pins, Attrs
from torii.platform.vendor.lattice.ecp5 import ECP5Platform

from ..                                 import ToriiToolchainTestCase, DUTCounter

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
		_ = platform.request('extref', 0)
		return m

class TestDCUElaboratable(Elaboratable):
	def __init__(self, mk_instance: bool = False) -> None:
		self.mk_instance = mk_instance

	def elaborate(self, platform: TestPlatform) -> Module:
		m = Module()
		dcu = platform.request('dcu', 0)

		if self.mk_instance:
			m.submodules.dcu_inst = Instance(
				'DCUA',
				i_CH0_HDINP  = dcu.rx.i_p[0],
				i_CH0_HDINN  = dcu.rx.i_n[0],
				o_CH0_HDOUTP = dcu.tx.o_p[0],
				o_CH0_HDOUTN = dcu.tx.o_n[0],
				i_CH1_HDINP  = dcu.rx.i_p[1],
				i_CH1_HDINN  = dcu.rx.i_n[1],
				o_CH1_HDOUTP = dcu.tx.o_p[1],
				o_CH1_HDOUTN = dcu.tx.o_n[1],
			)

		return m

class ECP5PlatformTestCase(TestCase):
	def test_inst_dcu_good(self):
		resource = Resource(
			'dcu', 0,
			Subsignal('tx', DiffPairs('W4 W8', 'W5 W9', dir = 'o')),
			Subsignal('rx', DiffPairs('Y5 Y7', 'Y6 Y8', dir = 'i')),
		)

		platform = TestPlatform()
		platform.add_resources((resource, ))

		plan = platform.prepare(TestDCUElaboratable(mk_instance = True))

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

		self.assertEqual(rtlil, r'''module \top.pin_dcu_0__tx
  wire width 2 output 0 \dcu_0__tx__p
  wire width 2 input 1 \dcu_0__tx__o_p
  wire width 2 output 2 \dcu_0__tx__n
  wire width 2 input 3 \dcu_0__tx__o_n
  process $group_0
    assign \dcu_0__tx__p 2'00
    assign \dcu_0__tx__p [0] \dcu_0__tx__o_p [0]
    assign \dcu_0__tx__p [1] \dcu_0__tx__o_p [1]
  end
  process $group_1
    assign \dcu_0__tx__n 2'00
    assign \dcu_0__tx__n [0] \dcu_0__tx__o_n [0]
    assign \dcu_0__tx__n [1] \dcu_0__tx__o_n [1]
  end
end
module \top.pin_dcu_0__rx
  wire width 2 output 0 \dcu_0__rx__i_p
  wire width 2 output 1 \dcu_0__rx__i_n
  wire width 2 input 2 \dcu_0__rx__p
  wire width 2 input 3 \dcu_0__rx__n
  process $group_0
    assign \dcu_0__rx__i_p 2'00
    assign \dcu_0__rx__i_p [0] \dcu_0__rx__p [0]
    assign \dcu_0__rx__i_p [1] \dcu_0__rx__p [1]
  end
  process $group_1
    assign \dcu_0__rx__i_n 2'00
    assign \dcu_0__rx__i_n [0] \dcu_0__rx__n [0]
    assign \dcu_0__rx__i_n [1] \dcu_0__rx__n [1]
  end
end
module \top
  wire width 2 output 0 \dcu_0__tx__p
  wire width 2 output 1 \dcu_0__tx__n
  wire width 2 input 2 \dcu_0__rx__p
  wire width 2 input 3 \dcu_0__rx__n
  wire width 2 \dcu_0__rx__i_p
  wire width 2 \dcu_0__rx__i_n
  wire width 2 \dcu_0__tx__o_p
  wire width 2 \dcu_0__tx__o_n
  cell \DCUA \dcu_inst
    connect \CH0_HDINP \dcu_0__rx__i_p [0]
    connect \CH0_HDINN \dcu_0__rx__i_n [0]
    connect \CH0_HDOUTP \dcu_0__tx__o_p [0]
    connect \CH0_HDOUTN \dcu_0__tx__o_n [0]
    connect \CH1_HDINP \dcu_0__rx__i_p [1]
    connect \CH1_HDINN \dcu_0__rx__i_n [1]
    connect \CH1_HDOUTP \dcu_0__tx__o_p [1]
    connect \CH1_HDOUTN \dcu_0__tx__o_n [1]
  end
  cell \top.pin_dcu_0__tx \pin_dcu_0__tx
    connect \dcu_0__tx__p \dcu_0__tx__p
    connect \dcu_0__tx__o_p \dcu_0__tx__o_p
    connect \dcu_0__tx__n \dcu_0__tx__n
    connect \dcu_0__tx__o_n \dcu_0__tx__o_n
  end
  cell \top.pin_dcu_0__rx \pin_dcu_0__rx
    connect \dcu_0__rx__i_p \dcu_0__rx__i_p
    connect \dcu_0__rx__i_n \dcu_0__rx__i_n
    connect \dcu_0__rx__p \dcu_0__rx__p
    connect \dcu_0__rx__n \dcu_0__rx__n
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
LOCATE COMP "dcu_0__tx__p[0]" SITE "W4";
LOCATE COMP "dcu_0__tx__p[1]" SITE "W8";
LOCATE COMP "dcu_0__tx__n[0]" SITE "W5";
LOCATE COMP "dcu_0__tx__n[1]" SITE "W9";
LOCATE COMP "dcu_0__rx__p[0]" SITE "Y5";
LOCATE COMP "dcu_0__rx__p[1]" SITE "Y7";
LOCATE COMP "dcu_0__rx__n[0]" SITE "Y6";
LOCATE COMP "dcu_0__rx__n[1]" SITE "Y8";
# (add_preferences placeholder)''')

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
  cell \EXTREFB \extref_0
    parameter \REFCK_DCBIAS_EN 1'1
    parameter \REFCK_RTERM 1'1
    parameter \REFCK_PWDNB 1'1
    connect \REFCLKP \extref_0__p
    connect \REFCLKN \extref_0__n
    connect \REFCLKO \extref_0__i
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


def trellis_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Trellis')(func)

def diamond_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Diamond')(func)

class ECP5ToolchainTests(ToriiToolchainTestCase[ECP5Platform]):
	TOOLCHAINS = ('Trellis', 'Diamond')

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
