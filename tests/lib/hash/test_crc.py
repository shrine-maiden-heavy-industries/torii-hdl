# SPDX-License-Identifier: BSD-2-Clause

from collections.abc    import Iterable

from zlib               import crc32

from torii.lib.hash.crc import BitwiseCRC, LUTBytewiseCRC, CombBytewiseCRC
from torii.test         import ToriiTestCase

from ...utils           import ToriiTestSuiteCase

CRC_DATA = b"Hello binary world"

def crc16_byte(data: int, bit_len: int, crc_in: int = 0) -> int:
	'''
	Computes the CRC16 of the given byte for the USB traffic.

	Parameters
	----------
	data : int
		The current byte to compute the CRC16 on.

	bit_len : int
		The number of bits of `data` to compute the CRC16 over.

	crc_in : int
		The result of a previous call to `crc16` if iterating over a buffer of data.

	Returns
	-------
	int
		The output CRC16 value.
	'''

	crc = int(f'{crc_in ^ 0xFFFF:016b}'[::-1], base = 2)

	for bit_idx in range(bit_len):
		bit = (data >> bit_idx) & 1
		crc <<= 1

		if bit != (crc >> 16):
			crc ^= 0x18005
		crc &= 0xFFFF

	crc ^= 0xFFFF
	return int(f'{crc:016b}'[::-1], base = 2)

@staticmethod
def crc16(data: Iterable[int]) -> int:
	'''
	Compute the CRC16 value of a buffer of bytes.

	Parameters
	----------
	data : Iterable[int]
		The buffer of bytes to compute the CRC16 for

	Returns
	-------
	int
		The CRC16 value of the data buffer.
	'''

	crc = 0
	for byte in data:
		crc = crc16_byte(byte, 8, crc)
	return crc

class BitwiseCRC32TestCase(ToriiTestSuiteCase):
	dut: BitwiseCRC = BitwiseCRC
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320,
		'data_width': 8,
		'crc_width': 32,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
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
		checkCRC = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield

class BitwiseCRC16TestCase(ToriiTestSuiteCase):
	dut: BitwiseCRC = BitwiseCRC
	dut_args = {
		# CRC-16 polynomial from USB for data packets
		'polynomial': 0xa001,
		'data_width': 8,
		'crc_width': 16,
		'reset_value': 0xffff,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
		yield
		# Now ask it to CRC the string "Hello binary world"
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

		# Use the above CRC-16 implementation to compute a reference value
		checkCRC = crc16(CRC_DATA)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
		yield

class LUTBytewiseCRC32TestCase(ToriiTestSuiteCase):
	dut: LUTBytewiseCRC = LUTBytewiseCRC
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320,
		'data_width': 8,
		'crc_width': 32,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
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
		checkCRC = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield

class LUTBytewiseCRC16TestCase(ToriiTestSuiteCase):
	dut: LUTBytewiseCRC = LUTBytewiseCRC
	dut_args = {
		# CRC-16 polynomial from USB for data packets
		'polynomial': 0xa001,
		'data_width': 8,
		'crc_width': 16,
		'reset_value': 0xffff,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
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
		# Use the above CRC-16 implementation to compute a reference value
		checkCRC = crc16(CRC_DATA)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
		yield

class CombBytewiseCRC32TestCase(ToriiTestSuiteCase):
	dut: CombBytewiseCRC = CombBytewiseCRC
	dut_args = {
		# CRC-32 polynomial most commonly used (PNG, Gzip, PKZIP, NVMe, SATA, Ethernet, etc)
		'polynomial': 0xedb88320,
		'data_width': 8,
		'crc_width': 32,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
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
		checkCRC = crc32(CRC_DATA, 0xffffffff)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0xffffffff)
		yield

class CombBytewiseCRC16TestCase(ToriiTestSuiteCase):
	dut: CombBytewiseCRC = CombBytewiseCRC
	dut_args = {
		# CRC-16 polynomial from USB for data packets
		'polynomial': 0xa001,
		'data_width': 8,
		'crc_width': 16,
		'reset_value': 0xffff,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_crc(self):
		# Check that the controller comes up into the proper state
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
		yield
		# Now ask it to CRC16 the string "Hello binary world"
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
		# Use the above CRC-16 implementation to compute a reference value
		checkCRC = crc16(CRC_DATA)
		# And check if the one computed matches
		self.assertEqual((yield self.dut.crc), checkCRC)
		yield

		# Finally, check if the reset signal works properly
		yield self.dut.reset.eq(1)
		yield
		yield self.dut.reset.eq(0)
		yield
		self.assertEqual((yield self.dut.done), 1)
		self.assertEqual((yield self.dut.crc), 0x0000)
		yield
