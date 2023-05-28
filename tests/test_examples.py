# SPDX-License-Identifier: BSD-2-Clause

import sys
import subprocess
from pathlib import Path

from .utils  import ToriiTestSuiteCase

EXAMPLE_DIR = (Path(__file__).parent / '..' / 'examples').resolve()
class ExamplesTestCase(ToriiTestSuiteCase):

	def _example_test(name: str):
		example_path = (EXAMPLE_DIR / name).resolve()

		def test_example(self):
			subprocess.check_call([
					sys.executable, str(example_path),
					'generate'
				],
				stdout = subprocess.DEVNULL
			)
		return test_example

	test_alu      = _example_test('basic/alu.py')
	test_alu_hier = _example_test('basic/alu_hier.py')
	test_arst     = _example_test('basic/arst.py')
	test_cdc      = _example_test('basic/cdc.py')
	test_ctr      = _example_test('basic/ctr.py')
	test_ctr_en   = _example_test('basic/ctr_en.py')
	test_fsm      = _example_test('basic/fsm.py')
	test_gpio     = _example_test('basic/gpio.py')
	test_inst     = _example_test('basic/inst.py')
	test_mem      = _example_test('basic/mem.py')
	test_pmux     = _example_test('basic/pmux.py')
	test_por      = _example_test('basic/por.py')
	test_uart     = _example_test('basic/uart.py')
