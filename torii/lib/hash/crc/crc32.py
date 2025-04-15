# SPDX-License-Identifier: BSD-2-Clause

from ....hdl.ast import Signal
from ....hdl.dsl import Module
from ....hdl.ir  import Elaboratable
from ....hdl.mem import Memory

__all__ = (
	'BitwiseCRC32',
)

class BitwiseCRC32(Elaboratable):
	def __init__(self, *, polynomial: int) -> None:
		# Reset the computed CRC32
		self.reset = Signal()
		# Input for the next byte of data to hash
		self.data = Signal(8)
		# Asserted for a cycle to indicate the data is valid
		self.valid = Signal()
		# The current computed CRC32
		self.crc = Signal(32)
		# Asserted when computation of the CRC32 is complete
		self.done = Signal()

		self._poly = polynomial

	def elaborate(self, _) -> Module:
		m = Module()

		data = Signal(32)
		bit = Signal(range(8))
		crc = Signal.like(self.crc)

		m.d.comb += [
			self.done.eq(0),
			self.crc.eq(~crc),
		]

		with m.FSM(name = 'crc32'):
			with m.State('IDLE'):
				# While idle, the output CRC is valid
				m.d.comb += self.done.eq(1)
				# If the user asks us to reset state
				with m.If(self.reset):
					# Put the CRC internal state back to the initial state
					m.d.sync += crc.eq(crc.reset)
				# If the user wants us to process another byte
				with m.Elif(self.valid):
					m.d.sync += data.eq(crc[0:8] ^ self.data)
					m.next = 'COMPUTE-CRC'

			with m.State('COMPUTE-CRC'):
				# For each bit in the value to process
				m.d.sync += bit.inc()
				# If we got to the last bit, we're done
				with m.If(bit == 7):
					m.next = 'DONE'

				# Compute the CRC for this bit
				with m.If(data & 1):
					m.d.sync += data.eq(self._poly ^ (data >> 1))
				with m.Else():
					m.d.sync += data.eq(data >> 1)

			with m.State('DONE'):
				# Copy the resulting CRC32 to our output
				m.d.sync += crc.eq(data ^ crc[8:32])
				m.next = 'IDLE'

		return m

class LUTBytewiseCRC32(Elaboratable):
	def __init__(self, *, polynomial: int) -> None:
		# Reset the computed CRC32
		self.reset = Signal()
		# Input for the next byte of data to hash
		self.data = Signal(8)
		# Asserted for a cycle to indicate the data is valid
		self.valid = Signal()
		# The current computed CRC32
		self.crc = Signal(32)
		# Asserted when computation of the CRC32 is complete
		self.done = Signal()

		self._poly = polynomial

	def elaborate(self, _) -> Module:
		m = Module()

		crc = Signal.like(self.crc)

		m.submodules.lut = lut = self.generate_rom()
		crcTable = lut.read_port()

		m.d.comb += [
			self.done.eq(0),
			self.crc.eq(~crc),
		]

		with m.FSM(name = 'crc32'):
			with m.State('IDLE'):
				# While idle, the output CRC is valid
				m.d.comb += self.done.eq(1)
				# If the user asks us to reset state
				with m.If(self.reset):
					# Put the CRC internal state back to the initial state
					m.d.sync += crc.eq(crc.reset)
				# If the user wants us to process another byte
				with m.Elif(self.valid):
					# Set up the access to the CRC fragment table
					m.d.comb += crcTable.addr.eq(crc[0:8] ^ self.data)
					m.next = 'COMPUTE-CRC'

			with m.State('COMPUTE-CRC'):
				# Take the resulting value from the fragment table, and combine it with
				# the previous CRC to generate the next one
				m.d.sync += crc.eq(crcTable.data ^ crc[8:32])
				m.next = 'IDLE'

		return m

	def compute_crc32(self, c: int, k: int) -> int:
		# If we've recursed through all bits in the byte, return the resulting CRC fragment
		if k == 0:
			return c
		# Otherwise, compute the next bit of the CRC fragment and recurse
		return self.compute_crc32((self._poly if (c & 1) == 1 else 0) ^ (c >> 1), k - 1)

	def generate_rom(self) -> Memory:
		# For each of the possible 256 byte values, compute the CRC32 fragment for that value
		crc32Table = tuple(self.compute_crc32(byte, 8) for byte in range(256))
		# Build a Memory from those values to be used in the FSM
		return Memory(width = 32, depth = 256, init = crc32Table)
