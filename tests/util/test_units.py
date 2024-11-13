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

	def test_log2_ceil(self):
		self.assertEqual(util_units.log2_ceil(0), 0)
		self.assertEqual(util_units.log2_ceil(1), 0)
		self.assertEqual(util_units.log2_ceil(2), 1)
		self.assertEqual(util_units.log2_ceil(3), 2)
		self.assertEqual(util_units.log2_ceil(4), 2)
		self.assertEqual(util_units.log2_ceil(5), 3)
		self.assertEqual(util_units.log2_ceil(8), 3)
		self.assertEqual(util_units.log2_ceil(9), 4)
		with self.assertRaises(TypeError):
			util_units.log2_ceil(1.5)
		with self.assertRaises(ValueError, msg = '-1 is negative'):
			util_units.log2_ceil(-1)

	def test_log2_exact(self):
		self.assertEqual(util_units.log2_exact(1), 0)
		self.assertEqual(util_units.log2_exact(2), 1)
		self.assertEqual(util_units.log2_exact(4), 2)
		self.assertEqual(util_units.log2_exact(8), 3)
		for val in [-1, 0, 3, 5, 6, 7, 9]:
			with self.assertRaises(ValueError, msg = f'{val} is not a power of 2'):
				util_units.log2_exact(val)
		with self.assertRaises(TypeError):
			util_units.log2_exact(1.5)

	def test_bits_for(self):
		self.assertEqual(util_units.bits_for(1024), 11)
		self.assertEqual(util_units.bits_for(-4), 3)
		self.assertEqual(util_units.bits_for(-3), 3)
		self.assertEqual(util_units.bits_for(-2), 2)
		self.assertEqual(util_units.bits_for(-1), 1)
		self.assertEqual(util_units.bits_for(0), 1)
		self.assertEqual(util_units.bits_for(1), 1)
		self.assertEqual(util_units.bits_for(2), 2)
		self.assertEqual(util_units.bits_for(3), 2)
		self.assertEqual(util_units.bits_for(4), 3)
		self.assertEqual(util_units.bits_for(5), 3)
		self.assertEqual(util_units.bits_for(-4, True), 3)
		self.assertEqual(util_units.bits_for(-3, True), 3)
		self.assertEqual(util_units.bits_for(-2, True), 2)
		self.assertEqual(util_units.bits_for(-1, True), 1)
		self.assertEqual(util_units.bits_for(0, True), 1)
		self.assertEqual(util_units.bits_for(1, True), 2)
		self.assertEqual(util_units.bits_for(2, True), 3)
		self.assertEqual(util_units.bits_for(3, True), 3)
		self.assertEqual(util_units.bits_for(4, True), 4)
		self.assertEqual(util_units.bits_for(5, True), 4)
