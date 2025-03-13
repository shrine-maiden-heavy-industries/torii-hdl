# SPDX-License-Identifier: BSD-2-Clause

from random                import randbytes

from torii.lib.coding.cobs import RCOBSEncoder, decode_rcobs
from torii.sim             import Settle
from torii.test            import ToriiTestCase

from ...utils              import ToriiTestSuiteCase

TEST_DATA = randbytes(512)

class rCOBSTestCase(ToriiTestSuiteCase):
	dut: RCOBSEncoder = RCOBSEncoder

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_encode(self):
		cobs_run = 0

		yield from self.step(5)

		for byte in TEST_DATA:
			cobs_run += 1

			yield from self.wait_until_high(self.dut.ready)
			yield self.dut.raw.eq(byte)
			yield self.dut.strobe.eq(1)
			yield Settle()
			yield
			yield self.dut.strobe.eq(0)
			yield Settle()
			yield
			yield from self.wait_until_high(self.dut.valid)

			if byte == 0:
				self.assertEqual((yield self.dut.enc), cobs_run)
				cobs_run = 0
			else:
				if cobs_run == 254:
					cobs_run = 0
					self.assertEqual((yield self.dut.enc), 0xFF)
				else:
					self.assertEqual((yield self.dut.enc), byte)

			yield self.dut.ack.eq(1)
			yield Settle()
			yield
			yield self.dut.ack.eq(0)

		yield self.dut.finish.eq(1)
		yield Settle()
		yield
		yield Settle()
		yield
		yield self.dut.finish.eq(0)
		yield from self.wait_until_high(self.dut.valid)
		self.assertEqual((yield self.dut.enc), cobs_run + 1)

	def test_decode(self):
		test_vectors = [
			(b'\x01', b''),
			(b'\x01\x01', b'\x00'),
			(b'\x01\x01\x01', b'\x00\x00'),
			(b'\x11\x22\x03\x33\x02', b'\x11\x22\x00\x33'),
			(b'\x11\x02\x01\x01\x01', b'\x11\x00\x00\x00'),
			(b'\x11\x22\x33\x44\x05', b'\x11\x22\x33\x44'),
		]

		for encoded, decoded in test_vectors:
			self.assertEqual(decode_rcobs(encoded), decoded)
