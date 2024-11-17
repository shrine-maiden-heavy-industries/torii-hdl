# SPDX-License-Identifier: BSD-2-Clause

import re
import subprocess
import warnings
from collections.abc import Callable
from pathlib         import Path
from typing          import Type, NamedTuple

from .               import has_tool, require_tool

__all__ = (
	'find_yosys',
	'YosysBinary',
	'YosysError',
)

class YosysVersion(NamedTuple):
	major: int
	minor: int
	distance: int

class YosysError(Exception):
	pass


class YosysWarning(Warning):
	pass


class YosysBinary:
	YOSYS_BINARY = 'yosys'

	@classmethod
	def available(cls: 'Type[YosysBinary]') -> bool:
		'''
		Check for Yosys availability.

		Returns
		-------
		available : bool
			``True`` if Yosys is installed, ``False`` otherwise. Installed binary may still not
			be runnable, or might be too old to be useful.

		'''

		return has_tool(cls.YOSYS_BINARY)

	@classmethod
	def version(cls: 'Type[YosysBinary]') -> YosysVersion | None:
		'''
		Get Yosys version.

		Returns
		-------
		``None`` if version number could not be determined, or a 3-tuple ``(major, minor, distance)`` if it could.

		major : int
			Major version.
		minor : int
			Minor version.
		distance : int
			Distance to last tag per ``git describe``. May not be exact for system Yosys.

		'''

		version = cls.run(['-V'])
		match = re.match(r'^Yosys (\d+)\.(\d+)(?:\+(\d+))?', version)
		if match:
			return YosysVersion(int(match[1]), int(match[2]), int(match[3] or 0))
		else:
			return None

	@classmethod
	def data_dir(cls: 'Type[YosysBinary]') -> Path:
		'''
		Get Yosys data directory.

		Returns
		-------
		data_dir : pathlib.Path
			Yosys data directory (also known as 'datdir').

		'''

		popen = subprocess.Popen(
			[require_tool(cls.YOSYS_BINARY) + '-config', '--datdir'],
			stdout = subprocess.PIPE, stderr = subprocess.PIPE,
			encoding = 'utf-8'
		)
		stdout, stderr = popen.communicate()
		if popen.returncode:
			raise YosysError(stderr.strip())
		return Path(stdout.strip())

	@classmethod
	def run(
		cls: 'Type[YosysBinary]', args: list[str], stdin: str = '', *, ignore_warnings: bool = False, src_loc_at: int = 0
	) -> str:
		'''
		Run Yosys process.

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

		Returns
		-------
		stdout : str
			Standard output.

		Exceptions
		----------
		YosysError
			Raised if Yosys returns a non-zero code. The exception message is the standard error
			output.

		'''

		popen = subprocess.Popen(
			[ require_tool(cls.YOSYS_BINARY), *args ],
			stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE,
			encoding = 'utf-8'
		)
		stdout, stderr = popen.communicate(stdin)
		# If Yosys is built with an evaluation version of Verific, then Verific license
		# information is printed first. It consists of empty lines and lines starting with `--`,
		# which are not normally a part of Yosys output, and can be fairly safely removed.
		#
		# This is not ideal, but Verific license conditions rule out any other solution.
		stdout = re.sub(r'\A(-- .+\n|\n)*', '', stdout)
		return cls._process_result(popen.returncode, stdout, stderr, ignore_warnings, src_loc_at)

	@classmethod
	def _process_result(
		cls: 'Type[YosysBinary]', returncode: int, stdout: str, stderr: str, ignore_warnings: bool, src_loc_at: int
	) -> str:
		if returncode:
			raise YosysError(stderr.strip())
		if not ignore_warnings:
			for match in re.finditer(r'(?ms:^Warning: (.+)\n$)', stderr):
				message = match.group(1).replace('\n', ' ')
				warnings.warn(message, YosysWarning, stacklevel = 3 + src_loc_at)
		return stdout

def min_yosys_version(version: YosysVersion) -> bool:
	'''
	Returns if the yosys version is greater than or equal to the minimum
	required version

	Parameters
	----------
	version: tuple[int, int, int]
		The version of Yosys found on the system

	Returns
	-------
	bool:
		If the version meets the minimum requirement. (currently 0.30+ except 0.37)

	'''

	return version >= (0, 30) and version != (0, 37)

def find_yosys(
	requirement: Callable[[YosysVersion], bool] = min_yosys_version
) -> type[YosysBinary]:
	'''
	Find an available Yosys executable of required version.

	Parameters
	----------
	requirement : function
		Version check. Should return ``True`` if the version is acceptable, ``False`` otherwise.

	Returns
	-------
	yosys_binary : subclass of YosysBinary
		Proxy for running the requested version of Yosys.

	Exceptions
	----------
	YosysError
		Raised if required Yosys version is not found.

	'''


	if YosysBinary.available():
		version = YosysBinary.version()
		if version is not None and requirement(version):
			return YosysBinary
	raise YosysError(
		'Could not find an acceptable Yosys binary.\n'
		'Please ensure it is in your path or you set YOSYS environment variable.'
	)
