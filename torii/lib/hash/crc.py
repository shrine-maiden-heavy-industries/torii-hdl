# SPDX-License-Identifier: BSD-2-Clause

from ...hdl.ast import Cat, Const, Signal, Slice, ValueDict
from ...hdl.dsl import Module
from ...hdl.ir  import Elaboratable
from ...hdl.mem import Memory
from ...util    import flatten

__all__ = (
	'BitwiseCRC',
	'LUTBytewiseCRC',
	'CombBytewiseCRC',
)

class BitwiseCRC(Elaboratable):
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, *, data_width: int, crc_width: int, polynomial: int, reset_value: int = 0, inverted_output: bool = True
	) -> None:
		# Reset the computed CRC
		self.reset = Signal()
		# Input for the next byte of data to hash
		self.data = Signal(data_width)
		# Asserted for a cycle to indicate the data is valid
		self.valid = Signal()
		# The current computed CRC
		self.crc = Signal(crc_width)
		# Asserted when computation of the CRC is complete
		self.done = Signal()

		self._poly = polynomial
		self._crc_reset_value = reset_value
		self._crc_inverted = inverted_output

	def elaborate(self, _) -> Module:
		m = Module()

		data_width = self.data.width
		crc_width = self.crc.width
		data = Signal(crc_width)
		bit = Signal(range(data_width))
		crc = Signal(crc_width, reset = self._crc_reset_value)

		m.d.comb += self.done.eq(0)

		if self._crc_inverted:
			m.d.comb += self.crc.eq(~crc)
		else:
			m.d.comb += self.crc.eq(crc)

		with m.FSM(name = 'crc'):
			with m.State('IDLE'):
				# While idle, the output CRC is valid
				m.d.comb += self.done.eq(1)
				# If the user asks us to reset state
				with m.If(self.reset):
					# Put the CRC internal state back to the initial state
					m.d.sync += crc.eq(crc.reset)
				# If the user wants us to process another byte
				with m.Elif(self.valid):
					m.d.sync += data.eq(crc[0:data_width] ^ self.data)
					m.next = 'COMPUTE-CRC'

			with m.State('COMPUTE-CRC'):
				# For each bit in the value to process
				m.d.sync += bit.inc()
				# If we got to the last bit, we're done
				with m.If(bit == data_width - 1):
					m.next = 'DONE'

				# Compute the CRC for this bit
				with m.If(data & 1):
					m.d.sync += data.eq(self._poly ^ (data >> 1))
				with m.Else():
					m.d.sync += data.eq(data >> 1)

			with m.State('DONE'):
				# Copy the resulting CRC to our output
				m.d.sync += [
					crc.eq(data ^ crc[data_width:]),
					bit.eq(0),
				]
				m.next = 'IDLE'

		return m

class LUTBytewiseCRC(Elaboratable):
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, *, data_width: int, crc_width: int, polynomial: int, reset_value: int = 0, inverted_output: bool = True
	) -> None:
		# Reset the computed CRC
		self.reset = Signal()
		# Input for the next byte of data to hash
		self.data = Signal(data_width)
		# Asserted for a cycle to indicate the data is valid
		self.valid = Signal()
		# The current computed CRC
		self.crc = Signal(crc_width)
		# Asserted when computation of the CRC is complete
		self.done = Signal()

		self._poly = polynomial
		self._crc_reset_value = reset_value
		self._crc_inverted = inverted_output

	def elaborate(self, _) -> Module:
		m = Module()

		data_width = self.data.width
		crc = Signal(self.crc.width, reset = self._crc_reset_value)

		m.submodules.lut = lut = self.generate_rom()
		crcTable = lut.read_port()

		m.d.comb += self.done.eq(0)

		if self._crc_inverted:
			m.d.comb += self.crc.eq(~crc)
		else:
			m.d.comb += self.crc.eq(crc)

		with m.FSM(name = 'crc'):
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
					m.d.comb += crcTable.addr.eq(crc[0:data_width] ^ self.data)
					m.next = 'COMPUTE-CRC'

			with m.State('COMPUTE-CRC'):
				# Take the resulting value from the fragment table, and combine it with
				# the previous CRC to generate the next one
				m.d.sync += crc.eq(crcTable.data ^ crc[data_width:])
				m.next = 'IDLE'

		return m

	def compute_crc(self, c: int, k: int) -> int:
		'''
		.. todo:: Document Me
		'''

		# If we've recursed through all bits in the byte, return the resulting CRC fragment
		if k == 0:
			return c
		# Otherwise, compute the next bit of the CRC fragment and recurse
		return self.compute_crc((self._poly if (c & 1) == 1 else 0) ^ (c >> 1), k - 1)

	def generate_rom(self) -> Memory:
		'''
		.. todo:: Document Me
		'''

		entries = 2 ** self.data.width
		# For each of the possible 256 byte values, compute the CRC32 fragment for that value
		crcTable = tuple(self.compute_crc(byte, 8) for byte in range(entries))
		# Build a Memory from those values to be used in the FSM
		return Memory(width = self.crc.width, depth = entries, init = crcTable)

class CombBytewiseCRC(Elaboratable):
	'''
	.. todo:: Document Me
	'''

	def __init__(
		self, *, data_width: int, crc_width: int, polynomial: int, reset_value: int = 0, inverted_output: bool = True
	) -> None:
		# Reset the computed CRC
		self.reset = Signal()
		# Input for the next byte of data to hash
		self.data = Signal(data_width)
		# Asserted for a cycle to indicate the data is valid
		self.valid = Signal()
		# The current computed CRC
		self.crc = Signal(crc_width)
		# Asserted when computation of the CRC is complete
		self.done = Signal()

		self._poly = polynomial
		self._crc_reset_value = reset_value
		self._crc_inverted = inverted_output

	def elaborate(self, _) -> Module:
		m = Module()

		crc = Signal(self.crc.width, reset = self._crc_reset_value)

		# We're always done, because of how things work.
		m.d.comb += self.done.eq(1)

		if self._crc_inverted:
			m.d.comb += self.crc.eq(~crc)
		else:
			m.d.comb += self.crc.eq(crc)

		# If the user asks us to reset state
		with m.If(self.reset):
			# Put the CRC internal state back to the initial state
			m.d.sync += crc.eq(crc.reset)
		# If the user wants us to process another byte
		with m.If(self.valid):
			# Consume that byte and compute the new CRC
			self.generateCRC(m, crc)

		return m

	def generateCRC(self, m: Module, crcSignal: Signal):
		'''
		.. todo:: Document Me
		'''

		polynomial = self._poly
		# Extract each individual bit into lists for both the input data and CRC
		data = [self.data[i] for i in range(self.data.width)]
		crc: list[Slice | list[Const | Slice]] = [crcSignal[i] for i in range(crcSignal.width)]

		# For each bit in the input data
		for dataBit in range(self.data.width):
			# Build a dictionary of state bits for every bit in the CRC signal
			stateBits = {i: [] for i in range(crcSignal.width)}
			# For each bit in the CRC
			for crcBit in range(crcSignal.width):
				# If the bit is not the last bit, grab the state for the next bit along, otherwise
				# use a constant 0 as a fill/default
				if crcBit != crcSignal.width - 1:
					stateBit = crc[crcBit + 1]
				else:
					stateBit = Const(0)
				# If the polynomial specifies a bit set at this position
				if polynomial & (1 << crcBit):
					# The state for this bit is the XOR between the state bit, the first bit of the CRC, and the data
					stateBits[crcBit] = [stateBit, crc[0], data[dataBit]]
				else:
					# Otherwise, it's just the selected state bit
					stateBits[crcBit] = [stateBit]

			# Having loops through all the bits in the CRC, optimise the resulting state vector
			for bit in range(crcSignal.width):
				# Start by flattening all the bit lists
				stateBit: list[Slice | Const] = list(flatten(stateBits[bit]))
				# With the flattening completed for this bit list, eliminate needless bits
				oneBits = 0
				signalBits = ValueDict[int]()
				# For each entry int he stateBit list
				for item in stateBit:
					# Test if that entry represents one of the input signal bits
					if isinstance(item, Slice):
						# Count how many times that bit has appeared
						signalBits[item] = signalBits.get(item, 0) + 1
					# Else if the entry represents a 1 bit, count that
					elif item.value == 1:
						oneBits += 1

				# Build the optimised signal bit vector for this bit ready for Cat
				result: list[Slice | Const] = []
				for signalBit, count in signalBits.items():
					if (count & 1) == 1:
						result.append(signalBit)
				if (oneBits & 1) == 1:
					result.append(Const(1))
				crc[bit] = result

		# We now have the equations, so build the CRC state update on sync:
		for bit in range(crcSignal.width):
			m.d.sync += crcSignal[bit].eq(Cat(crc[bit]).xor())
