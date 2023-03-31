# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

from torii.hdl                import *
from torii.asserts            import *
from torii.sim                import *
from torii.lib.coding.one_hot import Encoder, Decoder

from ...utils              import ToriiTestSuiteCase

class EncoderTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		enc = Encoder(4)

		def process():
			self.assertEqual((yield enc.n), 1)
			self.assertEqual((yield enc.o), 0)

			yield enc.i.eq(0b0001)
			yield Settle()
			self.assertEqual((yield enc.n), 0)
			self.assertEqual((yield enc.o), 0)

			yield enc.i.eq(0b0100)
			yield Settle()
			self.assertEqual((yield enc.n), 0)
			self.assertEqual((yield enc.o), 2)

			yield enc.i.eq(0b0110)
			yield Settle()
			self.assertEqual((yield enc.n), 1)
			self.assertEqual((yield enc.o), 0)

		sim = Simulator(enc)
		sim.add_process(process)
		sim.run()

class DecoderTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		dec = Decoder(4)

		def process():
			self.assertEqual((yield dec.o), 0b0001)

			yield dec.i.eq(1)
			yield Settle()
			self.assertEqual((yield dec.o), 0b0010)

			yield dec.i.eq(3)
			yield Settle()
			self.assertEqual((yield dec.o), 0b1000)

			yield dec.n.eq(1)
			yield Settle()
			self.assertEqual((yield dec.o), 0b0000)

		sim = Simulator(dec)
		sim.add_process(process)
		sim.run()
