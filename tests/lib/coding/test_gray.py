# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

from torii.hdl             import *
from torii.asserts         import *
from torii.sim             import *
from torii.lib.coding.gray import Encoder, Decoder

from ...utils              import ToriiTestSuiteCase

class ReversibleSpec(Elaboratable):
	def __init__(self, encoder_cls, decoder_cls, args):
		self.encoder_cls = encoder_cls
		self.decoder_cls = decoder_cls
		self.coder_args  = args

	def elaborate(self, platform):
		m = Module()
		enc, dec = self.encoder_cls(*self.coder_args), self.decoder_cls(*self.coder_args)
		m.submodules += enc, dec
		m.d.comb += [
			dec.i.eq(enc.o),
			Assert(enc.i == dec.o)
		]
		return m


class HammingDistanceSpec(Elaboratable):
	def __init__(self, distance, encoder_cls, args):
		self.distance    = distance
		self.encoder_cls = encoder_cls
		self.coder_args  = args

	def elaborate(self, platform):
		m = Module()
		enc1, enc2 = self.encoder_cls(*self.coder_args), self.encoder_cls(*self.coder_args)
		m.submodules += enc1, enc2
		m.d.comb += [
			Assume(enc1.i + 1 == enc2.i),
			Assert(sum(enc1.o ^ enc2.o) == self.distance)
		]
		return m


class GrayCoderTestCase(ToriiTestSuiteCase):
	def test_reversible(self):
		spec = ReversibleSpec(encoder_cls = Encoder, decoder_cls = Decoder, args = (16,))
		self.assertFormal(spec, mode = 'prove')

	def test_distance(self):
		spec = HammingDistanceSpec(distance = 1, encoder_cls = Encoder, args = (16,))
		self.assertFormal(spec, mode = 'prove')
