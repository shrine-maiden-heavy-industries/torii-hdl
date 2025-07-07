# SPDX-License-Identifier: BSD-2-Clause

from torii.lib.lfsr import LFSR, LFSRDir, LFSRKind
from torii.test     import ToriiTestCase

from ..utils        import ToriiTestSuiteCase

class LFSRTestCase(ToriiTestSuiteCase):
	dut: LFSR | type[LFSR] = LFSR
	dut_args = {
		'polynomial': (1 << 7) | (1 << 6) | (1 << 0), # x^7 + x^6 + x^0
		'state_width': 7,
		'io_width': 1,
		'seed': 0x2,
		'kind': LFSRKind.Galois,
		'direction': LFSRDir.LSb,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_lfsr(self):
		for _ in range(4096):
			yield
			yield


class LFSR2TestCase(ToriiTestSuiteCase):
	dut: LFSR | type[LFSR] = LFSR
	dut_args = {
		'polynomial': (1 << 16) | (1 << 14) | (1 << 13) | ( 1 << 11) | (1 << 0), # x^16 + x^14 + x^13 + x^11 + x^0
		'state_width': 16,
		'io_width': 1,
		'seed': 0xACE1,
		'kind': LFSRKind.Galois,
		'direction': LFSRDir.LSb,
	}

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_lfsr(self):
		for _ in range(4096):
			yield
			yield

class LFSR3TestCase(ToriiTestSuiteCase):
	dut: LFSR | type[LFSR] = LFSR
	dut_args = {
		'polynomial': (1 << 16) | (1 << 14) | (1 << 13) | ( 1 << 11) | (1 << 0), # x^16 + x^14 + x^13 + x^11 + x^0
		'state_width': 16,
		'io_width': 1,
		'seed': 0x8735,
		'kind': LFSRKind.Fibonacci,
		'direction': LFSRDir.LSb,
	}

	def setUp(self) -> None:
		super().setUp()
		from torii.back.verilog import convert
		with open('/tmp/lfsr.v', 'w') as f:
			lfsr = LFSR(**self.dut_args)
			f.write(convert(lfsr, 'lfsr', ports = [ lfsr._state, lfsr.input, lfsr.output ]))

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def test_lfsr(self):
		init = (yield self.dut._state)
		count = 0
		while True:
			count += 1
			yield
			if (yield self.dut._state) == init:
				yield
				break
