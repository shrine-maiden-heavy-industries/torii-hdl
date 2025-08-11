# SPDX-License-Identifier: BSD-2-Clause

import re
import warnings
from collections.abc import Callable
from pathlib         import Path
from subprocess      import PIPE, Popen
from typing          import NamedTuple

from ...tools       import has_tool, require_tool
from ...diagnostics import ToolWarning, ToolError

__all__ = (
	'VerilatorVersion',
	'VerilatorBinary',
	'find_verilator',
)

class VerilatorVersion(NamedTuple):
	major: int
	minor: int


class VerilatorBinary:
	VERILATOR_BINARY = 'verilator'

	@classmethod
	def available(cls: type['VerilatorBinary']) -> bool:
		'''
		Check for Verilator availability.

		Returns
		-------
		available : bool
			``True`` if Verilator is installed, ``False`` otherwise. Installed binary may still not
			be runnable, or might be too old to be useful.

		'''

		return has_tool(cls.VERILATOR_BINARY)

	@classmethod
	def version(cls: type['VerilatorBinary']) -> VerilatorVersion | None:
		'''
		Get Verilator version.

		Returns
		-------
		``None`` if version number could not be determined, or a tuple ``(major, minor)`` if it could.

		major : int
			Major version.

		minor : int
			Minor version.

		'''

		version = cls.run(['-V'])
		match = re.match(r'^Verilator (\d+)\.(\d+)\s', version)
		if match:
			return VerilatorVersion(int(match[1]), int(match[2]))
		else:
			return None

	@classmethod
	def data_dir(cls: type['VerilatorBinary']) -> Path | None:
		'''
		Get Verilator data directory.

		Returns
		-------
		data_dir : pathlib.Path | None
			Verilator data directory

		'''

		version = cls.run(['-V'])
		match = re.match(r'VERILATOR_ROOT\s+=\s([a-zA-Z\/]+)\n', version)
		if match:
			return Path(match[1])
		else:
			return None

	@classmethod
	def run(
		cls: type['VerilatorBinary'], args: list[str], stdin: str = '', *, ignore_warnings: bool = False,
		cwd: Path = Path.cwd()
	) -> str:
		'''
		Run Verilator process.

		Parameters
		----------
		args : list of str
			Arguments, not including the program name.

		stdin : str
			Standard input.

		ignore_warnings : bool
			Ignore any warnings produce

		src_loc_at : int
			Source location

		cwd : Path
			The working directory

		Returns
		-------
		stdout : str
			Standard output.

		Exceptions
		----------
		RuntimeError
			Raised if Verilator returns a non-zero code. The exception message is the standard error
			output.

		'''

		popen = Popen(
			[ require_tool(cls.VERILATOR_BINARY), *args ],
			stdin = PIPE, stdout = PIPE, stderr = PIPE,
			encoding = 'utf-8', cwd = cwd
		)
		stdout, stderr = popen.communicate(stdin)
		return cls._process_result(popen.returncode, stdout, stderr, ignore_warnings)

	@classmethod
	def _process_result(
		cls: type['VerilatorBinary'], returncode: int, stdout: str, stderr: str, ignore_warnings: bool
	) -> str:
		# if returncode:
		# 	raise ToolError(stderr.strip())
		if not ignore_warnings:
			for match in re.finditer(r'%Warning(-[A-Z0-9_]+)?: ((\S+):(\d+):((\d+):)? )?.*', stderr):
				message = ' '.join(filter(lambda g: g is not None, match.groups()))
				warnings.warn(message, ToolWarning, stacklevel = 3)
		return stdout

def min_verilator_version(version: VerilatorVersion) -> bool:
	'''
	Returns if the Verilator version is greater than or equal to the minimum
	required version

	Parameters
	----------
	version: tuple[int, int]
		The version of Verilator found on the system

	Returns
	-------
	bool:
		If the version meets the minimum requirement. (currently 5.31)

	'''

	return version >= (5, 31)

def find_verilator(
	requirement: Callable[[VerilatorVersion], bool] = min_verilator_version
) -> type['VerilatorBinary']:
	'''
	Find an available Verilator executable of required version.

	Parameters
	----------
	requirement : function
		Version check. Should return ``True`` if the version is acceptable, ``False`` otherwise.

	Returns
	-------
	VerilatorBinary
		Proxy for running the requested version of Verilator.

	Exceptions
	----------
	RuntimeError
		Raised if required Verilator version is not found.

	'''

	if VerilatorBinary.available():
		version = VerilatorBinary.version()
		if version is not None and requirement(version):
			return VerilatorBinary
	raise ToolError(
		'Could not find an acceptable Verilator binary.\n'
		'Please ensure it is in your path or you set VERILATOR environment variable.'
	)
