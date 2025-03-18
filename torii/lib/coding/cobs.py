# SPDX-License-Identifier: BSD-2-Clause

'''
This module implements some Consistent Overhead Byte Stuffing
(`COBS <https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing>`_) encoders, primarily the
:py:class:`RCOBSEncoder` which is well adept at streaming.

'''

from ...hdl.ast import Signal
from ...hdl.dsl import Module
from ...hdl.ir  import Elaboratable

__all__ = (
	'RCOBSEncoder',
	'decode_rcobs',
)

class RCOBSEncoder(Elaboratable):
	'''
	Reverse Consistent Overhead Byte Stuffing (rCOBS) encoder.

	This is an implementation of the rCOBS algorithm. The source of the encoding
	algorithm was originally a Rust crate and can be found at: https://github.com/Dirbaio/rcobs

	The algorithm is fairly simple, for each byte in a message, do the following for each byte:

		1. Increment the running total byte counter
		2. If the byte is ``0x00`` then write the value of the byte counter out and reset it to ``0``
		3. If it is not, then check to see if the running total counter is about to overflow
		4. If we are about to overflow, write out ``0xFF`` and reset the counter
		5. Otherwise, write out the byte

	This encoder is just a pure implementation of the encoding logic for a single byte, and as such
	has a collection of status and control signals to indicate to the outside world its status.

	For decoding rCOBS encoded messages the :py:func:`decode_rcobs` method implements that functionality
	for any host-side applications.

	Attributes
	----------
	raw : Signal(8), in
		The raw byte to encode.

	enc : Signal(8), out
		The rCOBS encoded byte. Not valid unless ``vld`` signal is high.

	strobe : Signal, in
		Strobe to signal to encode the byte in ``raw``.

	finish : Signal, in
		Flush the state of the encoder in preparation for next stream.

	ready : Signal, out
		Encoder ready signal, indicates when the encoder is ready for the next byte.

	valid : Signal, out
		Value in ``enc`` is valid and can be latched.

	'''

	def __init__(self) -> None:
		self.strobe = Signal()
		self.ready  = Signal()
		self.valid  = Signal()
		self.ack    = Signal()
		self.finish = Signal()

		self.run   = Signal(8)
		self.raw   = Signal(8)
		self.enc   = Signal.like(self.raw)

	def elaborate(self, _) -> Module:
		m = Module()

		with m.FSM(name = 'rcobs_encoder') as f:
			m.d.comb += [ self.ready.eq(f.ongoing('IDLE')), ]

			with m.State('IDLE'):
				with m.If(self.strobe):
					m.d.sync += [ self.run.inc(), ]
					m.next = 'ENC'
				with m.Elif(self.finish):
					m.d.sync += [
						self.enc.eq(self.run + 1),
						self.run.eq(0),
						self.valid.eq(1),
					]
					m.next = 'FINISH'

			with m.State('ENC'):
				m.d.sync += [ self.valid.eq(1), ]
				with m.If(self.raw == 0):
					# If the incoming byte is 0, then we write out the run and reset it
					m.d.sync += [
						self.enc.eq(self.run),
						self.run.eq(0),
					]
				with m.Else():
					# If the byte is non-zero, then we can just pass it along
					m.d.sync += [
						self.enc.eq(self.raw),
					]
					# If we have hit an almost max-run, then we need to reset the run and flag it
					with m.If(self.run == 254):
						# Emit a 0xFF byte and then reset the run
						m.d.sync += [
							self.enc.eq(0xFF),
							self.run.eq(0),
						]
				m.next = 'FINISH'
			with m.State('FINISH'):
				with m.If(self.ack):
					m.d.sync += [ self.valid.eq(0), ]
					m.next = 'IDLE'

		return m


def decode_rcobs(data: bytes | bytearray) -> bytes:
	'''
	Decode an rCOBS encoded message.

	The input data is expected to not contain any ``0x00`` framing information, it should be a single
	complete rCOBS message.

	Important
	---------
	This is not a synthesize construct, it is simply a helper function to decode messages produced with
	the :py:class:`RCOBSEncoder` on the host side. Or as a reference for implementation in other
	languages.

	Parameters
	----------
	data : bytes | bytearray
		The rCOBS encoded message.

	Returns
	-------
	bytes
		The rCOBS decoded message.

	Raises
	------
	ValueError
		If the input dat contains a ``0x00`` byte -OR- the message is improperly encoded.
	'''
	res     = bytearray(len(data))
	dat_idx = len(data)
	res_idx = len(res)

	while dat_idx != 0:
		byte = data[dat_idx - 1]
		if byte == 0x00:
			raise ValueError(f'Invalid rCOBS encoded byte at index {dat_idx} of input buffer')

		if byte != 0xFF:
			res_idx -= 1

		if dat_idx < byte:
			raise ValueError(f'Invalid rCOBS encoded byte at index {dat_idx} of input buffer')

		res[res_idx + 1 - byte:res_idx] = data[dat_idx - byte:dat_idx - 1]

		res_idx -= byte - 1
		dat_idx -= byte

	res = res[:len(data) - 1]
	return bytes(res[res_idx:])
