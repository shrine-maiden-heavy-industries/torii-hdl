# SPDX-License-Identifier: BSD-2-Clause

import warnings

from enum            import Enum, auto, unique

from ..hdl.ir        import Elaboratable
from ..hdl.dsl       import Module
from ..hdl.ast       import Cat, Const, Signal, ValueDict, Slice
from ..util.units    import bits_for
from ..util          import flatten

__all__ = (
	'LFSR',
	'LFSRKind',
	'LFSRDir',
)

@unique
class LFSRKind(Enum):
	Galois    = auto()
	Fibonacci = auto()

@unique
class LFSRDir(Enum):
	MSb = auto()
	LSb = auto()

class LFSR(Elaboratable):
	'''
	A simple linear-feedback shift register.

	Attributes
	----------
	state : Signal[width]
		The current state of the LFSR.

	Parameters
	----------
	polynomial : int
		The polynomial the LFSR implements.

	width : int
		How many bits wide the LFSR is.

	seed : int
		The initial starting seed value for the LFSR.
	'''

	def __init__(
		self, *, polynomial: int, state_width: int, io_width: int, seed: int, kind: LFSRKind, direction: LFSRDir
	) -> None:

		# Clip the seed so it fits into our LFSR
		poly_width = bits_for(polynomial)
		if poly_width > state_width + 1:
			warnings.warn(
				f'The polynomial {polynomial:X} is too wide for the LFSR ({poly_width} > {state_width}) '
				'and will be truncated.',
				RuntimeWarning, stacklevel = 2
			)

		# Enure the I/O width is correct for Fibonacci-type LFSRs
		if io_width != 1 and kind == LFSRKind.Fibonacci:
			raise ValueError('Fibonacci-type LFSRs can not have an IO width of more than one bit')

		self._seed = seed
		self._kind = kind
		self._dir  = direction

		# Adjust the polynomial so it's correct
		match self._dir:
			case LFSRDir.LSb:
				self._polynomial  = polynomial >> 1
			case LFSRDir.MSb:
				self._polynomial  = (polynomial << 1) & ((1 << poly_width) - 1)

		self._state = Signal(state_width, reset = seed)
		self._input = Signal(io_width)
		self.input  = Signal(io_width)
		self.output = Signal(io_width)

	def _generate_galois(self, m: Module) -> None:
		''' Generate an "optimized" Galois-type LFSR '''

		input_bits = [ self._input[bit] for bit in range(self._input.width) ]
		lfsr: list[Slice | list[Const | Slice]] = [ self._state[bit] for bit in range(self._state.width) ]

		for input_bit in input_bits:
			taps = { bit: [] for bit in range(self._state.width) }
			# Iterate over all the bits within the state vector
			for lfsr_bit in range(self._state.width):
				# Ensure the correct bit positions are picked depending on our shift-direction
				match self._dir:
					case LFSRDir.LSb:
						if lfsr_bit != self._state.width - 1:
							tap_bit = lfsr[lfsr_bit + 1]
						else:
							tap_bit = Const(0)
					case LFSRDir.MSb:
						if lfsr_bit != 0:
							tap_bit = lfsr[lfsr_bit - 1]
						else:
							tap_bit = Const(0)

				# Check to see if we need to insert a tap to XOR with the output
				if self._polynomial & (1 << lfsr_bit):
					taps[lfsr_bit] = [ tap_bit, input_bit ]
				else:
					taps[lfsr_bit] = [ tap_bit ]

			# Optimize the XOR expressions
			for bit in range(self._state.width):
				state_bit: list[Slice | Const] = list(flatten(taps[bit]))

				ones = 0
				signal_bits = ValueDict[int]()

				for signal_bit in state_bit:
					if isinstance(signal_bit, Slice):
						signal_bits[signal_bit] = signal_bits.get(signal_bit, 0) + 1
					elif signal_bit.value == 1:
						ones += 1

				result = list[Slice | Const]()

				for signal_bit, count in signal_bits.items():
					if (count & 1) == 1:
						result.append(signal_bit)
				if (ones & 1) == 1:
					result.append(Const(1))

				lfsr[bit] = result

		# Emit the XORs for all the taps after optimization
		for bit in range(self._state.width):
			m.d.sync += [
				self._state[bit].eq(Cat(lfsr[bit]).xor()),
			]

		# Hook up the output based on our direction
		match self._dir:
			case LFSRDir.LSb:
				m.d.comb += [
					self.output.eq(self._state[0]),
				]
			case LFSRDir.MSb:
				m.d.comb += [
					self.output.eq(self._state[-1]),
				]

	def _generate_fibonacci(self, m: Module) -> None:
		''' Generate a Fibonacci-style LFSR '''

		match self._dir:
			case LFSRDir.LSb:
				fib_in  = self._state[0]
				m.d.sync += [
					self._state.eq(self._state.shift_left(1))
				]
			case LFSRDir.MSb:
				fib_in  = self._state[-1]
				m.d.sync += [
					self._state.eq(self._state.shift_right(1))
				]

		taps = list[Slice]()

		# Find the taps
		for bit in range(self._state.width):
			if self._polynomial & (1 << bit):
				taps.append(self._state[bit])

		m.d.comb += [
			self.output.eq(Cat(taps).xor()),
		]

		m.d.sync += [
			fib_in.eq(self.input),
		]

	def elaborate(self, platform) -> Module:
		m = Module()

		# Stamp out the kind of LFSR we want to generate
		match self._kind:
			case LFSRKind.Galois:
				self._generate_galois(m)
			case LFSRKind.Fibonacci:
				self._generate_fibonacci(m)

		if False:
			m.d.comb += [
				self._input.eq(self.output ^ self.input)
			]
		else:
			m.d.comb += [
				self._input.eq(self.input)
			]

		# HACK(aki): Delete
		m.d.comb += [
			self.input.eq(self.output),
		]

		return m
