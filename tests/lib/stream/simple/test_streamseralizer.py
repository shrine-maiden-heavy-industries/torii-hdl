# SPDX-License-Identifier: BSD-2-Clause

from torii.lib.stream.simple.generator import StreamSerializer
from torii.test                        import ToriiTestCase

class StreamSerializerTestCase(ToriiTestCase):
	dut: StreamSerializer = StreamSerializer
	dut_args = {
		'data_length': 2, 'max_length_width': 2
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_basic(self):
		yield self.dut.max_length.eq(0b11)

		yield from self.step(4)
		self.assertEqual((yield self.dut.stream.valid), 0)
		self.assertEqual((yield self.dut.stream.first), 0)
		self.assertEqual((yield self.dut.stream.last), 0)

		# Load data into the serializer
		yield self.dut.data[0].eq(0b10101010)
		yield self.dut.data[1].eq(0b01010101)

		# Start transmission after a little bit
		yield from self.step(4)
		yield from self.pulse(self.dut.start)

		# Make sure the stream state is valid
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.first), 1)
		self.assertEqual((yield self.dut.stream.last), 0)
		# And that we've got the first byte of data
		self.assertEqual((yield self.dut.stream.data), 0b10101010)

		# Make sure it sticks there until it's ACK'd
		yield from self.step(16)
		self.assertEqual((yield self.dut.stream.data), 0b10101010)

		# Ack it
		yield self.dut.stream.ready.eq(1)
		yield

		# Get the last byte and make sure the stream state is correct
		yield
		self.assertEqual((yield self.dut.stream.data), 0b01010101)
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.first), 0)
		self.assertEqual((yield self.dut.stream.last), 1)

		# Check that the stream wraps up
		yield
		self.assertEqual((yield self.dut.stream.valid), 0)
		self.assertEqual((yield self.dut.stream.first), 0)
		self.assertEqual((yield self.dut.done), 1)
