# SPDX-License-Identifier: BSD-2-Clause

from random                  import randbytes

from torii.hdl.dsl           import Module
from torii.hdl.ir            import Elaboratable
from torii.lib.stream.simple import StreamArbiter, StreamInterface
from torii.sim.core          import Settle
from torii.test              import ToriiTestCase

from ...utils                import ToriiTestSuiteCase

class StreamInterfaceTestCase(ToriiTestSuiteCase):

	def test_record(self) -> None:
		s0 = StreamInterface()
		self.assertRepr(s0, '(rec s0 data valid first last ready)')

		s1 = StreamInterface(extra = [('meow', 8)])
		self.assertRepr(s1, '(rec s1 data valid first last ready meow)')

		s2 = StreamInterface(name = 'ULPI')
		self.assertRepr(s2, '(rec ULPI data valid first last ready)')

	def test_sizes(self) -> None:
		s0 = StreamInterface()
		self.assertEqual(s0.data.width,  8)
		self.assertEqual(s0.valid.width, 1)

		s1 = StreamInterface(data_width = 32, valid_width = None)
		self.assertEqual(s1.data.width,  32)
		self.assertEqual(s1.valid.width,  4)

		s2 = StreamInterface(data_width = 16, valid_width = 8)
		self.assertEqual(s2.data.width,  16)
		self.assertEqual(s2.valid.width,  8)

# TODO(aki): This test needs more proper assertions, the problem being is it's not super easy
#            to introspect, plus the StreamArbiter internals are actually kinda simple, so
#            this test is mostly just based on ✨ v i b e s ✨ and looking at the VCD :v

STREAM_DATA        = randbytes(512)
STREAM_DATA_STRIDE = len(STREAM_DATA) // 4

class StreamArbiterTestDUT(Elaboratable):
	arbiter: StreamArbiter
	s0: StreamInterface
	s1: StreamInterface
	s2: StreamInterface
	s3: StreamInterface

	def __init__(self) -> None:
		self.arbiter = StreamArbiter()
		self.s0 = StreamInterface()
		self.s1 = StreamInterface()
		self.s2 = StreamInterface()
		self.s3 = StreamInterface()

	def elaborate(self, _) -> Module:
		m = Module()

		m.submodules.arbiter = self.arbiter

		self.arbiter.connect(self.s0)
		self.arbiter.connect(self.s1)
		self.arbiter.connect(self.s2)
		self.arbiter.connect(self.s3)

		return m

class StreamArbiterTestCase(ToriiTestCase):
	dut      = StreamArbiterTestDUT
	dut_args = {}
	domains  = (('sync', 80e6), )

	@ToriiTestCase.simulation
	def test_arbiter(self):
		@ToriiTestCase.sync_domain(domain = 'sync')
		def s0_feeder(self: StreamArbiterTestCase):
			yield from self.step(5)
			for idx in range(STREAM_DATA_STRIDE):
				if idx == 0:
					yield self.dut.s0.first.eq(1)
				elif idx == STREAM_DATA_STRIDE - 1:
					yield self.dut.s0.last.eq(1)
				else:
					yield self.dut.s0.first.eq(0)
					yield self.dut.s0.last.eq(0)

				if (yield self.dut.s0.ready) == 1:
					yield self.dut.s0.data.eq(STREAM_DATA[idx])
				yield Settle()
				yield
			yield self.dut.s0.first.eq(0)
			yield self.dut.s0.last.eq(0)

		@ToriiTestCase.sync_domain(domain = 'sync')
		def s1_feeder(self: StreamArbiterTestCase):
			yield from self.step(3)
			for idx in range(STREAM_DATA_STRIDE):
				if idx == 0:
					yield self.dut.s1.first.eq(1)
				elif idx == STREAM_DATA_STRIDE - 1:
					yield self.dut.s1.last.eq(1)
				else:
					yield self.dut.s1.first.eq(0)
					yield self.dut.s1.last.eq(0)

				if (yield self.dut.s1.ready) == 1:
					yield self.dut.s1.data.eq(STREAM_DATA[idx + STREAM_DATA_STRIDE])
				yield Settle()
				yield
			yield self.dut.s1.first.eq(0)
			yield self.dut.s1.last.eq(0)

		@ToriiTestCase.sync_domain(domain = 'sync')
		def s2_feeder(self: StreamArbiterTestCase):
			yield from self.step(11)
			for idx in range(STREAM_DATA_STRIDE):
				if idx == 0:
					yield self.dut.s2.first.eq(1)
				elif idx == STREAM_DATA_STRIDE - 1:
					yield self.dut.s2.last.eq(1)
				else:
					yield self.dut.s2.first.eq(0)
					yield self.dut.s2.last.eq(0)

				if (yield self.dut.s2.ready) == 1:
					yield self.dut.s2.data.eq(STREAM_DATA[idx + (STREAM_DATA_STRIDE * 2)])
				yield Settle()
				yield
			yield self.dut.s2.first.eq(0)
			yield self.dut.s2.last.eq(0)

		@ToriiTestCase.sync_domain(domain = 'sync')
		def s3_feeder(self: StreamArbiterTestCase):
			yield from self.step(1)
			for idx in range(STREAM_DATA_STRIDE):
				if idx == 0:
					yield self.dut.s3.first.eq(1)
				elif idx == STREAM_DATA_STRIDE - 1:
					yield self.dut.s3.last.eq(1)
				else:
					yield self.dut.s3.first.eq(0)
					yield self.dut.s3.last.eq(0)

				if (yield self.dut.s3.ready) == 1:
					yield self.dut.s3.data.eq(STREAM_DATA[idx + (STREAM_DATA_STRIDE * 3)])
				yield Settle()
				yield
			yield self.dut.s3.first.eq(0)
			yield self.dut.s3.last.eq(0)

		@ToriiTestCase.sync_domain(domain = 'sync')
		def stream_arbiter(self: StreamArbiterTestCase):
			self.assertEqual((yield self.dut.arbiter.idle), 1)
			yield self.dut.arbiter.out.ready.eq(0)
			yield from self.step(10)
			yield self.dut.arbiter.out.ready.eq(1)
			yield self.dut.s0.valid.eq(1)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(1)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(1)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(1)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(1)
			yield self.dut.s1.valid.eq(1)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(1)
			yield self.dut.s2.valid.eq(1)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(1)
			yield self.dut.s3.valid.eq(1)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(1)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(1)
			yield from self.step(10)
			yield self.dut.s0.valid.eq(0)
			yield self.dut.s1.valid.eq(0)
			yield self.dut.s2.valid.eq(0)
			yield self.dut.s3.valid.eq(0)
			yield from self.step(10)

		s0_feeder(self)
		s1_feeder(self)
		s2_feeder(self)
		s3_feeder(self)
		stream_arbiter(self)
