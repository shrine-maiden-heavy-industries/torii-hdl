# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

import unittest

from torii                  import *
from torii.lib.fifo         import SyncFIFO
from torii.lib.io           import pin_layout
from torii.sim              import *

from torii.lib.stdio.serial import *


def simulation_test(dut, process):
	sim = Simulator(dut)
	with sim.write_vcd('test.vcd'):
		sim.add_clock(1e-6)
		sim.add_sync_process(process)
		sim.run()


class AsyncSerialRXTestCase(unittest.TestCase):
	def tx_period(self):
		for _ in range((yield self.dut.divisor)):
			yield

	def tx_bits(self, bits):
		for bit in bits:
			yield from self.tx_period()
			yield self.dut.i.eq(bit)

	def rx_test(self, bits, *, data = None, errors = None):
		def process():
			self.assertFalse((yield self.dut.rdy))
			yield self.dut.ack.eq(1)
			yield from self.tx_bits(bits)
			while not (yield self.dut.rdy):
				yield
			if data is not None:
				self.assertFalse((yield self.dut.err.overflow))
				self.assertFalse((yield self.dut.err.frame))
				self.assertFalse((yield self.dut.err.parity))
				self.assertEqual((yield self.dut.data), data)
			if errors is not None:
				for error in errors:
					self.assertTrue((yield getattr(self.dut.err, error)))
		simulation_test(self.dut, process)

	def test_invalid_divisor(self):
		with self.assertRaisesRegex(
			ValueError,
			r'Invalid divisor 1; must be greater than or equal to 5'
		):
			self.dut = AsyncSerialRX(divisor = 1)

	def test_invalid_parity(self):
		with self.assertRaisesRegex(
			ValueError,
			r'Invalid parity \'bad\'; must be one of none, mark, space, even, odd'
		):
			self.dut = AsyncSerialRX(divisor = 5, parity = 'bad')

	def test_8n1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 8, parity = 'none')
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 1], data = 0b01110101)

	def test_16n1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 16, parity = 'none')
		self.rx_test(
			[0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1],
			data = 0b0000111101110101
		)

	def test_8m1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 8, parity = 'mark')
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1], data = 0b01110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1], data = 0b00110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1], errors = {'parity'})

	def test_8s1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 8, parity = 'space')
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1], data = 0b01110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1], data = 0b00110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1], errors = {'parity'})

	def test_8e1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 8, parity = 'even')
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1], data = 0b01110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1], data = 0b00110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1], errors = {'parity'})

	def test_8o1(self):
		self.dut = AsyncSerialRX(divisor = 5, data_bits = 8, parity = 'odd')
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1], data = 0b01110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1], data = 0b00110101)
		self.rx_test([0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1], errors = {'parity'})

	def test_err_frame(self):
		self.dut = AsyncSerialRX(divisor = 5)
		self.rx_test([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], errors = {'frame'})

	def test_err_overflow(self):
		self.dut = AsyncSerialRX(divisor = 5)

		def process():
			self.assertFalse((yield self.dut.rdy))
			yield from self.tx_bits([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
			yield from self.tx_period()
			yield
			self.assertFalse((yield self.dut.rdy))
			self.assertTrue((yield self.dut.err.overflow))

		simulation_test(self.dut, process)

	def test_fifo(self):
		self.dut  = AsyncSerialRX(divisor = 5)
		self.fifo = SyncFIFO(width = 8, depth = 4)
		m = Module()
		m.submodules.rx   = self.dut
		m.submodules.fifo = self.fifo
		m.d.comb += [
			self.dut.ack.eq(self.fifo.w_rdy),
			self.fifo.w_en.eq(self.dut.rdy),
			self.fifo.w_data.eq(self.dut.data),
		]

		def process():
			yield from self.tx_bits([
				0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
				0, 0, 1, 0, 1, 0, 1, 0, 1, 1
			])
			self.assertTrue((yield self.fifo.r_rdy))
			self.assertEqual((yield self.fifo.r_data), 0x55)
			yield self.fifo.r_en.eq(1)
			yield
			yield
			while not (yield self.fifo.r_rdy):
				yield
			self.assertEqual((yield self.fifo.r_data), 0xAA)
			yield
			self.assertFalse((yield self.fifo.r_rdy))

		simulation_test(m, process)


class AsyncSerialTXTestCase(unittest.TestCase):
	def tx_period(self):
		for _ in range((yield self.dut.divisor)):
			yield

	def tx_test(self, data, *, bits):
		def process():
			self.assertTrue((yield self.dut.rdy))
			yield self.dut.data.eq(data)
			yield self.dut.ack.eq(1)
			while (yield self.dut.rdy):
				yield
			for bit in bits:
				yield from self.tx_period()
				self.assertEqual((yield self.dut.o), bit)

		simulation_test(self.dut, process)

	def test_invalid_divisor(self):
		with self.assertRaisesRegex(
			ValueError,
			r'Invalid divisor 0; must be greater than or equal to 1'
		):
			self.dut = AsyncSerialTX(divisor = 0)

	def test_invalid_parity(self):
		with self.assertRaisesRegex(
			ValueError,
			r'Invalid parity \'bad\'; must be one of none, mark, space, even, odd'
		):
			self.dut = AsyncSerialTX(divisor = 1, parity = 'bad')

	def test_8n1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 8, parity = 'none')
		self.tx_test(0b01110101, bits = [0, 1, 0, 1, 0, 1, 1, 1, 0, 1])

	def test_16n1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 16, parity = 'none')
		self.tx_test(0b0000111101110101, bits = [
			0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1
		])

	def test_8m1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 8, parity = 'mark')
		self.tx_test(0b01110101, bits = [0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1])
		self.tx_test(0b00110101, bits = [0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1])

	def test_8s1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 8, parity = 'space')
		self.tx_test(0b01110101, bits = [0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1])
		self.tx_test(0b00110101, bits = [0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1])

	def test_8e1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 8, parity = 'even')
		self.tx_test(0b01110101, bits = [0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1])
		self.tx_test(0b00110101, bits = [0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1])

	def test_8o1(self):
		self.dut = AsyncSerialTX(divisor = 1, data_bits = 8, parity = 'odd')
		self.tx_test(0b01110101, bits = [0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1])
		self.tx_test(0b00110101, bits = [0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1])

	def test_fifo(self):
		self.dut  = AsyncSerialTX(divisor = 1)
		self.fifo = SyncFIFO(width = 8, depth = 4)
		m = Module()
		m.submodules.tx   = self.dut
		m.submodules.fifo = self.fifo
		m.d.comb += [
			self.dut.ack.eq(self.fifo.r_rdy),
			self.dut.data.eq(self.fifo.r_data),
			self.fifo.r_en.eq(self.fifo.r_rdy & self.dut.rdy),
		]

		def process():
			self.assertTrue((yield self.fifo.w_rdy))
			yield self.fifo.w_en.eq(1)
			yield self.fifo.w_data.eq(0x55)
			yield
			self.assertTrue((yield self.fifo.w_rdy))
			yield self.fifo.w_data.eq(0xAA)
			yield
			yield self.fifo.w_en.eq(0)
			yield
			for bit in [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]:
				yield from self.tx_period()
				self.assertEqual((yield self.dut.o), bit)
			yield
			for bit in [0, 0, 1, 0, 1, 0, 1, 0, 1, 1]:
				yield from self.tx_period()
				self.assertEqual((yield self.dut.o), bit)

		simulation_test(m, process)


class AsyncSerialTestCase(unittest.TestCase):
	def test_loopback(self):
		pins = Record([
			('rx', pin_layout(1, dir = 'i')),
			('tx', pin_layout(1, dir = 'o'))
		])
		self.dut = AsyncSerial(divisor = 5, pins = pins)
		m = Module()
		m.submodules.serial = self.dut
		m.d.comb += pins.rx.i.eq(pins.tx.o)

		def process():
			self.assertTrue((yield self.dut.tx.rdy))
			yield self.dut.tx.data.eq(0xAA)
			yield self.dut.tx.ack.eq(1)
			yield
			yield self.dut.tx.ack.eq(0)
			yield self.dut.rx.ack.eq(1)
			yield
			while not (yield self.dut.rx.rdy):
				yield
			self.assertEqual((yield self.dut.rx.data), 0xAA)

		simulation_test(m, process)
