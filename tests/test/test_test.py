# SPDX-License-Identifier: BSD-2-Clause

from torii      import Elaboratable, Module, Signal
from torii.sim  import Settle
from torii.test import ToriiTestCase

class TestSyncDUT(Elaboratable):
	def __init__(self) -> None:
		self.a = Signal(reset = 1)
		self.b = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()

		m.d.sync += [
			self.b.eq(self.a),
			self.a.eq(~self.a),
		]

		return m

class TestMultiSyncDUT(Elaboratable):
	def __init__(self) -> None:
		self.a = Signal(reset = 1)
		self.b = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()

		m.d.sync1 += [
			self.a.eq(~self.a),
		]

		m.d.sync2 += [
			self.b.eq(~self.b),
		]

		return m


class ToriiTestCaseSyncTest(ToriiTestCase):
	domains = (('sync', 1e6), )
	dut: TestSyncDUT = TestSyncDUT

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_sync(self):
		self.assertEqual((yield self.dut.a), 1)
		yield Settle()
		yield
		self.assertEqual((yield self.dut.a), 0)
		self.assertEqual((yield self.dut.b), 1)
		yield Settle()
		yield
		yield Settle()
		yield

class ToriiTestCaseMultiSyncTest(ToriiTestCase):
	domains = (('sync1', 1e6), ('sync2', 2e6), )
	dut: TestMultiSyncDUT = TestMultiSyncDUT

	@ToriiTestCase.simulation
	def test_multi_sync(self):
		@ToriiTestCase.sync_domain(domain = 'sync1')
		def sync1(self):
			self.assertEqual((yield self.dut.a), 1)
			yield Settle()
			yield
			yield from self.step(100)

		@ToriiTestCase.sync_domain(domain = 'sync2')
		def sync2(self):
			self.assertEqual((yield self.dut.b), 0)
			yield Settle()
			yield
			yield from self.step(100)

		# Invoke sync process setup, this won't actually run the sim it just
		# ensures that the process defined by the function is added to the
		# simulator.
		sync1(self)
		sync2(self)
