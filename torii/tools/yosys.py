# SPDX-License-Identifier: BSD-2-Clause

from __future__      import annotations

import re
import subprocess
import warnings
from collections.abc import Callable
from pathlib         import Path
from typing          import NamedTuple

from ..diagnostics   import YosysError, YosysWarning
from .               import has_tool, require_tool

__all__ = (
	'find_yosys',
	'YosysBinary',
)

class YosysVersion(NamedTuple):
	''' A 3-tuple that contains the Yosys version in the form of ``(major, minor, distance)`` '''

	major: int
	minor: int
	distance: int

class YosysBinary:
	''' Represents a Yosys binary that lives somewhere on the system. '''

	YOSYS_BINARY = 'yosys'

	@classmethod
	def available(cls: type[YosysBinary]) -> bool:
		'''
		Check to see if we can find a Yosys binary on the system via the ``PATH`` or alternative
		lookup methods. See :py:func:`has_tool <torii.tools.has_tool>` for more information on the
		lookup preformed.

		Returns
		-------
		bool
			``True`` if Yosys is installed, ``False`` otherwise. Installed binary may still not
			be runnable, or might be too old to be useful.
		'''

		return has_tool(cls.YOSYS_BINARY)

	@classmethod
	def version(cls: type[YosysBinary]) -> YosysVersion | None:
		'''
		Return the version of the Yosys binary installed on the system.

		Returns
		-------
		YosysVersion | None
			The version of Yosys found, otherwise ``None`` if we are unable to determine the version.
		'''

		version = cls.run(['-V'])
		match = re.match(r'^Yosys (\d+)\.(\d+)(?:\+(\d+))?', version)
		if match:
			return YosysVersion(int(match[1]), int(match[2]), int(match[3] or 0))
		else:
			return None

	@classmethod
	def data_dir(cls: type[YosysBinary]) -> Path:
		'''
		Return the path to the data directory for the Yosys installed on the system.

		Returns
		-------
		pathlib.Path
			The path to the Yosys data directory.

		Raises
		------
		torii.diagnostics.YosysError
			If the invocation of Yosys failed for any reason. The error message will be the contents
			of standard error.
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
		cls: type[YosysBinary], args: list[str], stdin: str = '', *, ignore_warnings: bool = False, src_loc_at: int = 0
	) -> str:
		'''
		Run Yosys with the given arguments, and standard input.

		Parameters
		----------
		args: list[str]
			Arguments to pass to the invocation of the Yosys process.

		stdin: str
			Commands or other information to be fed to the standard input of the Yosys process.

		ignore_warnings: bool
			Ignore any warnings that Yosys generates.

		src_loc_at: int
			The source location to adjust the warning context to so Yosys warnings
			do not originate at the call site for ``run``.

		Returns
		-------
		str
			The contents of ``stdout`` from the Yosys process.

		Raises
		------
		torii.diagnostics.YosysError
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
		cls: type[YosysBinary], returncode: int, stdout: str, stderr: str, ignore_warnings: bool, src_loc_at: int
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
	required version for Torii.

	Note
	----
	The current Version requirement for Yosys is ``>=0.30,!=0.37``.

	Parameters
	----------
	version: YosysVersion
		The version of Yosys found on the system

	Returns
	-------
	bool
		If the version meets the minimum requirement.
	'''

	return version >= (0, 30) and version != (0, 37)

def find_yosys(
	requirement: Callable[[YosysVersion], bool] = min_yosys_version
) -> type[YosysBinary]:
	'''
	Attempt to find a valid Yosys install on the host system that matches the given version
	requirement.

	Parameters
	----------
	requirement: collections.abc.Callable[[YosysVersion], bool]
		The method used to check to make sure the found version of Yosys is valid. Should return ``True``
		if it is, otherwise ``False``.

	Returns
	-------
	type[YosysBinary]
		Proxy for running the requested version of Yosys.

	Raises
	------
	torii.diagnostics.YosysError
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
