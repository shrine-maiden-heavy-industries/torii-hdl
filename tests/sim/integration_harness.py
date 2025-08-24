# SPDX-License-Identifier: BSD-2-Clause

import os
from warnings        import catch_warnings

from torii.hdl.ast   import Array, Fell, Past, Rose, Signal, Stable, ValueCastable,  unsigned
from torii.hdl.cd    import ClockDomain
from torii.hdl.dsl   import Module
from torii.hdl.mem   import Memory
from torii.sim       import Delay, Passive, Settle, Simulator, Tick

from ._harness_types import SimulatorIntegrationTestMixinBase

class SimulatorIntegrationTestsMixin(SimulatorIntegrationTestMixinBase):

	def setUp_counter(self):
		self.count = Signal(3, reset = 4)
		self.sync  = ClockDomain()

		self.m = Module()
		self.m.d.sync  += self.count.eq(self.count + 1)
		self.m.domains += self.sync

	def test_counter_process(self):
		self.setUp_counter()
		with self.assertSimulation(self.m) as sim:

			def process():
				self.assertEqual((yield self.count), 4)
				yield Delay(1e-6)
				self.assertEqual((yield self.count), 4)
				yield self.sync.clk.eq(1)
				self.assertEqual((yield self.count), 4)
				yield Settle()
				self.assertEqual((yield self.count), 5)
				yield Delay(1e-6)
				self.assertEqual((yield self.count), 5)
				yield self.sync.clk.eq(0)
				self.assertEqual((yield self.count), 5)
				yield Settle()
				self.assertEqual((yield self.count), 5)
				for _ in range(3):
					yield Delay(1e-6)
					yield self.sync.clk.eq(1)
					yield Delay(1e-6)
					yield self.sync.clk.eq(0)
				self.assertEqual((yield self.count), 0)

			sim.add_process(process)

	def test_counter_clock_and_sync_process(self):
		self.setUp_counter()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6, domain = 'sync')

			def process():
				self.assertEqual((yield self.count), 4)
				self.assertEqual((yield self.sync.clk), 1)
				yield
				self.assertEqual((yield self.count), 5)
				self.assertEqual((yield self.sync.clk), 1)
				for _ in range(3):
					yield
				self.assertEqual((yield self.count), 0)

			sim.add_sync_process(process)

	def test_reset(self):
		self.setUp_counter()
		sim = Simulator(self.m)
		sim.add_clock(1e-6)
		times = 0

		def process():
			nonlocal times
			self.assertEqual((yield self.count), 4)
			yield
			self.assertEqual((yield self.count), 5)
			yield
			self.assertEqual((yield self.count), 6)
			yield
			times += 1

		sim.add_sync_process(process)
		sim.run()
		sim.reset()
		sim.run()
		self.assertEqual(times, 2)

	def setUp_alu(self):
		self.a = Signal(8)
		self.b = Signal(8)
		self.o = Signal(8)
		self.x = Signal(8)
		self.s = Signal(2)
		self.sync = ClockDomain(reset_less = True)

		self.m = Module()
		self.m.d.comb += self.x.eq(self.a ^ self.b)
		with self.m.Switch(self.s):
			with self.m.Case(0):
				self.m.d.sync += self.o.eq(self.a + self.b)
			with self.m.Case(1):
				self.m.d.sync += self.o.eq(self.a - self.b)
			with self.m.Default():
				self.m.d.sync += self.o.eq(0)
		self.m.domains += self.sync

	def test_alu(self):
		self.setUp_alu()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6)

			def process():
				yield self.a.eq(5)
				yield self.b.eq(1)
				yield
				self.assertEqual((yield self.x), 4)
				yield
				self.assertEqual((yield self.o), 6)
				yield self.s.eq(1)
				yield
				yield
				self.assertEqual((yield self.o), 4)
				yield self.s.eq(2)
				yield
				yield
				self.assertEqual((yield self.o), 0)

			sim.add_sync_process(process)

	def setUp_clock_phase(self):
		self.m = Module()
		self.phase0 = self.m.domains.phase0 = ClockDomain()
		self.phase90 = self.m.domains.phase90 = ClockDomain()
		self.phase180 = self.m.domains.phase180 = ClockDomain()
		self.phase270 = self.m.domains.phase270 = ClockDomain()
		self.check = self.m.domains.check = ClockDomain()

		self.expected = [
			[0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
			[0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1],
			[0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1],
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
		]

	def test_clock_phase(self):
		self.setUp_clock_phase()
		with self.assertSimulation(self.m) as sim:
			period = 1
			sim.add_clock(period / 8, phase = 0,              domain = 'check')
			sim.add_clock(period,     phase = 0 * period / 4, domain = 'phase0')
			sim.add_clock(period,     phase = 1 * period / 4, domain = 'phase90')
			sim.add_clock(period,     phase = 2 * period / 4, domain = 'phase180')
			sim.add_clock(period,     phase = 3 * period / 4, domain = 'phase270')

			def proc():
				clocks = [
					self.phase0.clk,
					self.phase90.clk,
					self.phase180.clk,
					self.phase270.clk
				]
				for i in range(16):
					yield
					for j, c in enumerate(clocks):
						self.assertEqual((yield c), self.expected[j][i])

			sim.add_sync_process(proc, domain = 'check')

	def setUp_multiclock(self):
		self.sys = ClockDomain()
		self.pix = ClockDomain()

		self.m = Module()
		self.m.domains += self.sys, self.pix

	def test_multiclock(self):
		self.setUp_multiclock()
		with self.assertSimulation(self.m) as sim:
			sim.add_clock(1e-6, domain = 'sys')
			sim.add_clock(0.3e-6, domain = 'pix')

			def sys_process():
				yield Passive()
				yield
				yield
				self.fail()

			def pix_process():
				yield
				yield
				yield

			sim.add_sync_process(sys_process, domain = 'sys')
			sim.add_sync_process(pix_process, domain = 'pix')

	def setUp_lhs_rhs(self):
		self.i = Signal(8)
		self.o = Signal(8)

		self.m = Module()
		self.m.d.comb += self.o.eq(self.i)

	def test_complex_lhs_rhs(self):
		self.setUp_lhs_rhs()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.i.eq(0b10101010)
				yield self.i[:4].eq(-1)
				yield Settle()
				self.assertEqual((yield self.i[:4]), 0b1111)
				self.assertEqual((yield self.i), 0b10101111)
			sim.add_process(process)

	def test_run_until(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertSimulation(m, deadline = 100e-6) as sim:
			sim.add_clock(1e-6)

			def process():
				for _ in range(101):
					yield Delay(1e-6)
				self.fail()
			sim.add_process(process)

	def test_run_until_fail(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertRaises(AssertionError):
			with self.assertSimulation(m, deadline = 100e-6) as sim:
				sim.add_clock(1e-6)

				def process():
					for _ in range(99):
						yield Delay(1e-6)
					self.fail()
				sim.add_process(process)

	def test_add_process_wrong(self):
		with self.assertSimulation(Module()) as sim:
			with self.assertRaisesRegex(
				TypeError,
				r'^Cannot add a process 1 because it is not a generator function$'
			):
				sim.add_process(1)

	def test_add_process_wrong_generator(self):
		with self.assertSimulation(Module()) as sim:
			with self.assertRaisesRegex(
				TypeError,
				r'^Cannot add a process <.+?> because it is not a generator function$'
			):
				def process():
					yield Delay()
				sim.add_process(process())

	def test_add_clock_wrong_twice(self):
		m = Module()
		s = Signal()
		m.d.sync += s.eq(0)
		with self.assertSimulation(m) as sim:
			sim.add_clock(1)
			with self.assertRaisesRegex(
				ValueError,
				r'^Domain \'sync\' already has a clock driving it$'
			):
				sim.add_clock(1)

	def test_add_clock_wrong_missing(self):
		m = Module()
		with self.assertSimulation(m) as sim:
			with self.assertRaisesRegex(
				ValueError,
				r'^Domain \'sync\' is not present in simulation$'
			):
				sim.add_clock(1)

	def test_add_clock_if_exists(self):
		m = Module()
		with self.assertSimulation(m) as sim:
			sim.add_clock(1, if_exists = True)

	def test_command_wrong(self):
		survived = False
		with self.assertSimulation(Module()) as sim:
			def process():
				nonlocal survived

				with self.assertRaisesRegex(
					TypeError,
					r'Received unsupported command 1 from process .+'
				):
					yield 1
				# yield Settle()
				survived = True
			sim.add_process(process)
		self.assertTrue(survived)

	def test_value_castable(self):
		class MyValue(ValueCastable):
			@ValueCastable.lowermethod
			def as_value(self):
				return Signal()

			def shape():
				return unsigned(1)

		a = Array([1, 2, 3])
		a[MyValue()]

		survived = False
		with self.assertSimulation(Module()) as sim:
			def process():
				nonlocal survived
				yield MyValue()
				survived = True
			sim.add_process(process)
		self.assertTrue(survived)

	def setUp_memory(self, rd_synchronous = True, rd_transparent = True, wr_granularity = None):
		self.m = Module()
		self.memory = Memory(width = 8, depth = 4, init = [0xaa, 0x55])
		self.m.submodules.rdport = self.rdport = self.memory.read_port(
			domain = 'sync' if rd_synchronous else 'comb',
			transparent = rd_transparent
		)
		self.m.submodules.wrport = self.wrport = self.memory.write_port(
			granularity = wr_granularity
		)

	def test_memory_init(self):
		self.setUp_memory()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.rdport.addr.eq(1)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x55)
				yield self.rdport.addr.eq(2)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x00)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write(self):
		self.setUp_memory()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.addr.eq(4)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				yield self.wrport.en.eq(0)
				yield self.rdport.addr.eq(4)
				yield
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write_granularity(self):
		self.setUp_memory(wr_granularity = 4)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x50)
				yield self.wrport.en.eq(0b00)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.wrport.en.eq(0b10)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0x5a)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(0b01)
				yield
				yield self.wrport.en.eq(0)
				yield
				self.assertEqual((yield self.rdport.data), 0x53)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_read_before_write(self):
		self.setUp_memory(rd_transparent = False)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_write_through(self):
		self.setUp_memory(rd_transparent = True)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
				yield
				yield self.rdport.addr.eq(1)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_async_read_write(self):
		self.setUp_memory(rd_synchronous = False)
		with self.assertSimulation(self.m) as sim:
			def process():
				yield self.rdport.addr.eq(0)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.rdport.addr.eq(1)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x55)
				yield self.rdport.addr.eq(0)
				yield self.wrport.addr.eq(0)
				yield self.wrport.data.eq(0x33)
				yield self.wrport.en.eq(1)
				yield Tick('sync')
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield Settle()
				self.assertEqual((yield self.rdport.data), 0x33)
			sim.add_clock(1e-6)
			sim.add_process(process)

	def test_memory_read_only(self):
		self.m = Module()
		self.memory = Memory(width = 8, depth = 4, init = [0xaa, 0x55])
		self.m.submodules.rdport = self.rdport = self.memory.read_port()
		with self.assertSimulation(self.m) as sim:
			def process():
				yield
				self.assertEqual((yield self.rdport.data), 0xaa)
				yield self.rdport.addr.eq(1)
				yield
				yield
				self.assertEqual((yield self.rdport.data), 0x55)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_transparency_simple(self):
		m = Module()
		init = (0x11, 0x22, 0x33, 0x44)
		m.submodules.memory = memory = Memory(width = 8, depth = 4, init = init)
		rdport = memory.read_port()
		wrport = memory.write_port(granularity = 8)
		with self.assertSimulation(m) as sim:
			def process():
				yield rdport.addr.eq(0)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x11)
				yield rdport.addr.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22)
				yield wrport.addr.eq(0)
				yield wrport.data.eq(0x44444444)
				yield wrport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22)
				yield wrport.addr.eq(1)
				yield wrport.data.eq(0x55)
				yield wrport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x55)
				yield wrport.addr.eq(1)
				yield wrport.data.eq(0x66)
				yield wrport.en.eq(1)
				yield rdport.en.eq(0)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x55)
				yield wrport.addr.eq(2)
				yield wrport.data.eq(0x77)
				yield wrport.en.eq(1)
				yield rdport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x66)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_memory_transparency_multibit(self):
		m = Module()
		init = (0x11111111, 0x22222222, 0x33333333, 0x44444444)
		m.submodules.memory = memory = Memory(width = 32, depth = 4, init = init)
		rdport = memory.read_port()
		wrport = memory.write_port(granularity = 8)
		with self.assertSimulation(m) as sim:
			def process():
				yield rdport.addr.eq(0)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x11111111)
				yield rdport.addr.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22222222)
				yield wrport.addr.eq(0)
				yield wrport.data.eq(0x44444444)
				yield wrport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22222222)
				yield wrport.addr.eq(1)
				yield wrport.data.eq(0x55555555)
				yield wrport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22222255)
				yield wrport.addr.eq(1)
				yield wrport.data.eq(0x66666666)
				yield wrport.en.eq(2)
				yield rdport.en.eq(0)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22222255)
				yield wrport.addr.eq(1)
				yield wrport.data.eq(0x77777777)
				yield wrport.en.eq(4)
				yield rdport.en.eq(1)
				yield
				yield Settle()
				self.assertEqual((yield rdport.data), 0x22776655)
			sim.add_clock(1e-6)
			sim.add_sync_process(process)

	def test_sample_helpers(self):
		m = Module()
		s = Signal(2)

		def mk(x):
			y = Signal.like(x)
			m.d.comb += y.eq(x)
			return y

		p0, r0, f0, s0 = mk(Past(s, 0)), mk(Rose(s)),    mk(Fell(s)),    mk(Stable(s))
		p1, r1, f1, s1 = mk(Past(s)),    mk(Rose(s, 1)), mk(Fell(s, 1)), mk(Stable(s, 1))
		p2, r2, f2, s2 = mk(Past(s, 2)), mk(Rose(s, 2)), mk(Fell(s, 2)), mk(Stable(s, 2))
		p3, r3, f3, s3 = mk(Past(s, 3)), mk(Rose(s, 3)), mk(Fell(s, 3)), mk(Stable(s, 3))
		with self.assertSimulation(m) as sim:
			def process_gen():
				yield s.eq(0b10)
				yield
				yield
				yield s.eq(0b01)
				yield

			def process_check():
				yield
				yield
				yield

				self.assertEqual((yield p0), 0b01)
				self.assertEqual((yield p1), 0b10)
				self.assertEqual((yield p2), 0b10)
				self.assertEqual((yield p3), 0b00)

				self.assertEqual((yield s0), 0b0)
				self.assertEqual((yield s1), 0b1)
				self.assertEqual((yield s2), 0b0)
				self.assertEqual((yield s3), 0b1)

				self.assertEqual((yield r0), 0b01)
				self.assertEqual((yield r1), 0b00)
				self.assertEqual((yield r2), 0b10)
				self.assertEqual((yield r3), 0b00)

				self.assertEqual((yield f0), 0b10)
				self.assertEqual((yield f1), 0b00)
				self.assertEqual((yield f2), 0b00)
				self.assertEqual((yield f3), 0b00)
			sim.add_clock(1e-6)
			sim.add_sync_process(process_gen)
			sim.add_sync_process(process_check)

	def test_vcd_wrong_nonzero_time(self):
		s = Signal()
		m = Module()
		m.d.sync += s.eq(s)
		sim = Simulator(m)
		sim.add_clock(1e-6)
		sim.run_until(1e-5)
		with self.assertRaisesRegex(
			ValueError,
			r'^Cannot start writing waveforms after advancing simulation time$'
		):
			with open(os.path.devnull, 'w') as f:
				with sim.write_vcd(f):
					pass # :nocov:

	def test_no_negated_boolean_warning(self):
		m = Module()
		a = Signal()
		b = Signal()
		m.d.comb += a.eq(~(b == b))
		with catch_warnings(record=True) as warns:
			Simulator(m).run()
			self.assertEqual(warns, [])

	def test_large_expr_parser_overflow(self):
		m = Module()
		a = Signal()

		op = a
		for _ in range(50):
			op = (op ^ 1)

		op = op & op

		m.d.comb += a.eq(op)
		Simulator(m)

	def test_switch_zero(self):
		m = Module()
		a = Signal(0)
		o = Signal()
		with m.Switch(a):
			with m.Case(''):
				m.d.comb += o.eq(1)
		with self.assertSimulation(m) as sim:
			def process():
				yield Settle()
				self.assertEqual((yield o), 1)
			sim.add_process(process)

	def test_switch_any(self):
		m = Module()
		a = Signal(3)
		o = Signal(3)
		with m.Switch(a):
			with m.Case('0-0'):
				m.d.comb += o.eq(0b000)
			with m.Case('0-1'):
				m.d.comb += o.eq(0b001)
			with m.Case('1-0'):
				m.d.comb += o.eq(0b100)
			with m.Case('1-1'):
				m.d.comb += o.eq(0b101)

		with self.assertSimulation(m) as sim:
			def process():
				yield a.eq(0b000)
				yield Settle()
				self.assertEqual((yield o), 0)
				yield a.eq(0b010)
				yield Settle()
				self.assertEqual((yield o), 0)
				yield a.eq(0b001)
				yield Settle()
				self.assertEqual((yield o), 1)
				yield a.eq(0b011)
				yield Settle()
				self.assertEqual((yield o), 1)
				yield a.eq(0b100)
				yield Settle()
				self.assertEqual((yield o), 0b100)
				yield a.eq(0b110)
				yield Settle()
				self.assertEqual((yield o), 0b100)
				yield a.eq(0b101)
				yield Settle()
				self.assertEqual((yield o), 0b101)
				yield a.eq(0b111)
				yield Settle()
				self.assertEqual((yield o), 0b101)

			sim.add_process(process)
