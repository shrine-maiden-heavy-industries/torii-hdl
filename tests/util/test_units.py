# SPDX-License-Identifier: BSD-2-Clause

from torii.util import units as util_units
from torii.test import ToriiTestCase

class UnitUtilTestCase(ToriiTestCase):

	def test_time_conversion(self):
		self.assertEqual(util_units.ns_to_sec(183.0), 0.000000183)
		self.assertEqual(util_units.sec_to_ns(0.000000183), 183)
		self.assertEqual(util_units.us_to_sec(24), 0.000024)
		self.assertEqual(util_units.sec_to_us(0.000024), 24)
		self.assertEqual(util_units.ms_to_sec(32.5), 0.0325)
		self.assertEqual(util_units.sec_to_ms(0.0325), 32.5)

	def test_iec_size(self):
		self.assertEqual(util_units.iec_size(1032), '1.01KiB')

		self.assertEqual(util_units.iec_size(256, dec = 0), '256B')

		self.assertEqual(
			util_units.iec_size(18446744073509553615, dec = 10),
			'15.9999999998EiB'
		)

	def test_log2_int(self):
		self.assertEqual(util_units.log2_int(0), 0)
		self.assertEqual(util_units.log2_int(4), 2)
		self.assertEqual(util_units.log2_int(9, False), 4)

		with self.assertRaisesRegex(ValueError, r'^\d is not a power of 2$'):
			util_units.log2_int(3)

	def test_bits_for(self):
		self.assertEqual(util_units.bits_for(1024), 11)
		self.assertEqual(util_units.bits_for(-3), 3)
