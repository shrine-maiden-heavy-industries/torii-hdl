# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

from torii.hdl                 import *
from torii.asserts             import *
from torii.sim                 import *
from torii.lib.coding.priority import Encoder

from ...utils                  import ToriiTestSuiteCase


class PriorityEncoderTestCase(ToriiTestSuiteCase):
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
			self.assertEqual((yield enc.n), 0)
			self.assertEqual((yield enc.o), 1)

		sim = Simulator(enc)
		sim.add_process(process)
		sim.run()
