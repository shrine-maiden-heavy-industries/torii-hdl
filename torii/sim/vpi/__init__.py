# SPDX-License-Identifier: BSD-2-Clause

from abc             import ABCMeta, abstractmethod
from os              import environ
from pathlib         import Path
from subprocess      import PIPE, Popen
from tempfile        import TemporaryDirectory
from typing          import Literal, TypeAlias

from ...back.verilog import convert_fragment
from ...hdl.ir       import Fragment
from ...tools        import require_tool
from .._base         import BaseEngine, BaseSignalState, BaseSimulation
from .verilator      import find_verilator

__all__ = (
	'VerilatorSimEngine',
	'VPIBackend',
	'VPISimEngine',
)

VPIBackend: TypeAlias = Literal['verilator']

def _run_make(cwd: Path, args: list[str]) -> tuple[str, str]:
	popen = Popen(
		[ require_tool('make'), *args ],
		stdin = PIPE, stdout = PIPE, stderr = PIPE,
		encoding = 'utf-8', cwd = cwd
	)

	return popen.communicate()


class _VPISimulationBase(BaseSimulation, metaclass = ABCMeta):
	@abstractmethod
	def build_vpi_driver(self, fragment: Fragment) -> None:
		raise NotImplementedError

class _VerilatorSignalState(BaseSignalState):
	pass

class _VerilatorSimulation(_VPISimulationBase):
	def __init__(self) -> None:
		self._working_dir_temp = TemporaryDirectory(
			prefix = 'torii_vpi_',
			delete = environ.get('TORII_VPI_KEEP') is None
		)
		self._working_dir = Path(self._working_dir_temp.name).resolve()

		self._top_name  = 'top'
		self._dut_file  = self._working_dir / 'top.v'
		self._obj_dir   = self._working_dir / 'build'
		self._src_dir   = self._working_dir / 'srcs'
		self._verilator = find_verilator()
		self._signals   = None

	def build_vpi_driver(self, fragment: Fragment) -> None:
		with self._dut_file.open('w') as f:
			verilog, signals = convert_fragment(fragment, name = self._top_name)
			f.write(verilog)

			self._signals = signals

		# Build Verilated DUT
		self._verilator.run([
			'--cc',
			'--vpi',
			'--public-flat-rw',
			'-Mdir', str(self._src_dir),
			'--top-module', self._top_name,
			'--trace',
			'--prefix', 'Vtop',
			str(self._dut_file)
		], cwd = self._working_dir)

		# Compile library
		_run_make(self._src_dir, [
			'-f', 'Vtop.mk', 'libVtop'
		])

	def reset(self) -> None:
		pass

	def get_signal(self, signal) -> None:
		pass

	def add_trigger(self, process, signal, *, trigger=None):
		pass

	def remove_trigger(self, process, signal):
		pass

	def wait_interval(self, process, interval):
		pass

class VPISimEngine(BaseEngine):
	_sim: _VPISimulationBase

	def __init__(self, fragment: Fragment, *, vpi_backend: VPIBackend = 'verilator') -> None:
		self._frag = fragment

		match vpi_backend:
			case 'verilator':
				self._sim = _VerilatorSimulation()
			case _:
				raise NotImplementedError(f'Unknown VPI backend {vpi_backend}')

		self._sim.build_vpi_driver(self._frag)

	def add_coroutine_process(self, process, *, default_cmd):
		pass

	def add_clock_process(self, clock, *, phase, period):
		pass

	def reset(self):
		pass

	def advance(self):
		return True

	@property
	def now(self):
		return 0

# TODO(aki): This might be able to be replaced with `functools.partial`
def VerilatorSimEngine(fragment: Fragment) -> VPISimEngine:
	return VPISimEngine(fragment = fragment, vpi_backend = 'verilator')
