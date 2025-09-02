# SPDX-License-Identifier: BSD-2-Clause

from torii.lib.stream.simple.generator import ConstantStreamGenerator
from torii.test                        import ToriiTestCase

class ConstantStreamGeneratorTestCase(ToriiTestCase):
	dut: ConstantStreamGenerator = ConstantStreamGenerator
	dut_args = {
		'data': b'NYA MEOW MEOW NYA',
		'max_length_width': 16
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_basic(self):
		# Set a large max-length so we don't apply it on the short message
		yield self.dut.max_len.eq(1024)

		# Make sure that we've not started after a handful of cycles
		yield from self.step(16)
		self.assertEqual((yield self.dut.stream.valid), 0)
		self.assertEqual((yield self.dut.stream.first), 0)
		self.assertEqual((yield self.dut.stream.last), 0)

		# Pulse start and check to see if we've started transmitting the messages
		yield from self.pulse(self.dut.start)
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][0])
		self.assertEqual((yield self.dut.stream.first), 1)

		# Make sure the data sticks until we ACK it
		yield from self.step(16)
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][0])

		# Start accepting the data
		yield self.dut.stream.ready.eq(1)
		yield

		# Accept some more data
		for byte in self.dut_args['data'][1:8]:
			yield
			self.assertEqual((yield self.dut.stream.valid), 1)
			self.assertEqual((yield self.dut.stream.data), byte)
			self.assertEqual((yield self.dut.stream.first), 0)

		# Stop being able to accept data, and make sure we do get the next byte
		yield self.dut.stream.ready.eq(0)
		yield
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][8])

		# We've not ACK'd it, so it should stick
		yield
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][8])

		yield self.dut.stream.ready.eq(1)
		yield

		# Accept the rest of the data
		for byte in self.dut_args['data'][9:]:
			yield
			self.assertEqual((yield self.dut.stream.valid), 1)
			self.assertEqual((yield self.dut.stream.data), byte)

		# On the last byte, make sure the stream sets `last`
		self.assertEqual((yield self.dut.stream.last), 1)

		# Past the last byte `valid` should go low
		yield
		self.assertEqual((yield self.dut.stream.valid), 0)

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_basic_start(self):
		# Set the stream start position to be the 3rd byte
		yield self.dut.start_pos.eq(2)

		# Set a large max-length so we don't apply it on the short message
		yield self.dut.max_len.eq(1024)

		# Make sure that we've not started after a handful of cycles
		yield from self.step(16)
		self.assertEqual((yield self.dut.stream.valid), 0)
		self.assertEqual((yield self.dut.stream.first), 0)
		self.assertEqual((yield self.dut.stream.last), 0)

		# Pulse start and check to see if we've started transmitting the messages
		yield from self.pulse(self.dut.start)
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][2])
		self.assertEqual((yield self.dut.stream.first), 1)

		# Make sure the data sticks until we ACK it
		yield from self.step(16)
		self.assertEqual((yield self.dut.stream.valid), 1)
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][2])

		# Start accepting the data
		yield self.dut.stream.ready.eq(1)
		yield

		# Accept some more data
		for byte in self.dut_args['data'][3:9]:
			yield
			self.assertEqual((yield self.dut.stream.valid), 1)
			self.assertEqual((yield self.dut.stream.data), byte)
			self.assertEqual((yield self.dut.stream.first), 0)

		# Stop being able to accept data, and make sure we do get the next byte
		yield self.dut.stream.ready.eq(0)
		yield
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][9])

		# We've not ACK'd it, so it should stick
		yield
		self.assertEqual((yield self.dut.stream.data), self.dut_args['data'][9])

		yield self.dut.stream.ready.eq(1)
		yield

		# Accept the rest of the data
		for byte in self.dut_args['data'][10:]:
			yield
			self.assertEqual((yield self.dut.stream.valid), 1)
			self.assertEqual((yield self.dut.stream.data), byte)

		# On the last byte, make sure the stream sets `last`
		self.assertEqual((yield self.dut.stream.last), 1)

		# Past the last byte `valid` should go low
		yield
		self.assertEqual((yield self.dut.stream.valid), 0)

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_max_length(self):
		# Set the max length to the first 4 bytes, and tell the generator we're ready
		yield self.dut.stream.ready.eq(1)
		yield self.dut.max_len.eq(4)

		# Start receiving the data
		yield from self.pulse(self.dut.start)

		for byte in self.dut_args['data'][0:3]:
			self.assertEqual((yield self.dut.stream.data), byte)
			yield

		# On the last byte, make sure the stream sets `last`
		self.assertEqual((yield self.dut.stream.last), 1)

		# Past the last byte `valid` should go low
		yield
		self.assertEqual((yield self.dut.stream.valid), 0)
