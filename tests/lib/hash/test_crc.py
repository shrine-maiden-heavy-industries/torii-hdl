# SPDX-License-Identifier: BSD-2-Clause

from zlib               import crc32

from torii.lib.hash.crc import BitwiseCRC32, LUTBytewiseCRC32, CombBytewiseCRC32
from torii.test         import ToriiTestCase

from ...utils          import ToriiTestSuiteCase

CRC_DATA = b"Hello binary world"

class BitwiseCRC32TestCase(ToriiTestSuiteCase):
	dut: BitwiseCRC32 = BitwiseCRC32
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc32(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield
		# Now ask it to CRC32 the string "Hello binary world"
		for byte in CRC_DATA:
			# Load the byte to CRC
			yield self.dut.data.eq(byte)
			yield self.dut.valid.eq(1)
			yield
			self.assertEqual((yield self.dut.done), 1)
			yield self.dut.data.eq(0)
			yield self.dut.valid.eq(0)
			yield
			self.assertEqual((yield self.dut.done), 0)
			# Wait for the computation to complete
			yield from self.wait_until_high(self.dut.done)

		# Use the zlib module from the stdlib to compute a reference value
		checkCRC32 = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC32)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield

class LUTBytewiseCRC32TestCase(ToriiTestSuiteCase):
	dut: LUTBytewiseCRC32 = LUTBytewiseCRC32
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc32(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield
		# Now ask it to CRC32 the string "Hello binary world"
		for byte in CRC_DATA:
			# Load the byte to CRC
			yield self.dut.data.eq(byte)
			yield self.dut.valid.eq(1)
			yield
			self.assertEqual((yield self.dut.done), 1)
			yield self.dut.data.eq(0)
			yield self.dut.valid.eq(0)
			yield
			self.assertEqual((yield self.dut.done), 0)
			# Computation will complete in the next cycle, so no worries there

		yield
		self.assertEqual((yield self.dut.done), 1)
		# Use the zlib module from the stdlib to compute a reference value
		checkCRC32 = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC32)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield

class CombBytewiseCRC32TestCase(ToriiTestSuiteCase):
	dut: CombBytewiseCRC32 = CombBytewiseCRC32
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc32(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield
		# Now ask it to CRC32 the string "Hello binary world"
		for byte in CRC_DATA:
			# Load the byte to CRC
			yield self.dut.data.eq(byte)
			yield self.dut.valid.eq(1)
			yield
			self.assertEqual((yield self.dut.done), 1)
			yield self.dut.data.eq(0)
			yield self.dut.valid.eq(0)
			yield
			self.assertEqual((yield self.dut.done), 1)

		yield
		self.assertEqual((yield self.dut.done), 1)
		# Use the zlib module from the stdlib to compute a reference value
		checkCRC32 = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC32)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield
