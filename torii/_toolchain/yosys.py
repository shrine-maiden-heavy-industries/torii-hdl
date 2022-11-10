# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import re
import subprocess
import warnings
from pathlib   import Path
from importlib import metadata, resources
from typing    import List, Tuple, Callable, Optional

from .         import has_tool, require_tool

__all__ = (
	'YosysError',
	'YosysBinary',
	'find_yosys',
)

class YosysError(Exception):
	pass


class YosysWarning(Warning):
	pass


class YosysBinary:
	@classmethod
	def available(cls) -> bool:
		'''Check for Yosys availability.

		Returns
		-------
		available : bool
			``True`` if Yosys is installed, ``False`` otherwise. Installed binary may still not
			be runnable, or might be too old to be useful.
		'''
		raise NotImplementedError

	@classmethod
	def version(cls) -> Optional[Tuple[int, int, int]]:
		'''Get Yosys version.

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
		raise NotImplementedError

	@classmethod
	def data_dir(cls) -> Path:
		'''Get Yosys data directory.

		Returns
		-------
		data_dir : pathlib.Path
			Yosys data directory (also known as 'datdir').
		'''
		raise NotImplementedError

	@classmethod
	def run(
		cls, args : List[str], stdin : str = '', *, ignore_warnings : bool = False, src_loc_at : int = 0
	) -> str:
		'''Run Yosys process.

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
		raise NotImplementedError

	@classmethod
	def _process_result(
		cls, returncode : int, stdout : str, stderr : str, ignore_warnings : bool, src_loc_at : int
	) -> str:
		if returncode:
			raise YosysError(stderr.strip())
		if not ignore_warnings:
			for match in re.finditer(r'(?ms:^Warning: (.+)\n$)', stderr):
				message = match.group(1).replace('\n', ' ')
				warnings.warn(message, YosysWarning, stacklevel = 3 + src_loc_at)
		return stdout


class _BuiltinYosys(YosysBinary):
	YOSYS_PACKAGE = 'amaranth_yosys'

	@classmethod
	def available(cls) -> bool:
		try:
			metadata.version(cls.YOSYS_PACKAGE)
			return True
		except metadata.PackageNotFoundError:
			return False

	@classmethod
	def version(cls) -> Tuple[int, int, int]:
		version = metadata.version(cls.YOSYS_PACKAGE)
		match = re.match(r'^(\d+)\.(\d+)(?:\.post(\d+))?', version)
		return (int(match[1]), int(match[2]), int(match[3] or 0))

	@classmethod
	def data_dir(cls) -> Path:
		return resources.files(cls.YOSYS_PACKAGE) / 'share'

	@classmethod
	def run(
		cls, args : List[str], stdin : str = '', *, ignore_warnings : bool = False, src_loc_at : int = 0
	) -> str:
		popen = subprocess.Popen(
			[ sys.executable, '-m', cls.YOSYS_PACKAGE, *args ],
			stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE,
			encoding = 'utf-8'
		)
		stdout, stderr = popen.communicate(stdin)
		return cls._process_result(popen.returncode, stdout, stderr, ignore_warnings, src_loc_at)


class _SystemYosys(YosysBinary):
	YOSYS_BINARY = 'yosys'

	@classmethod
	def available(cls) -> bool:
		return has_tool(cls.YOSYS_BINARY)

	@classmethod
	def version(cls) -> Optional[Tuple[int, int, int]]:
		version = cls.run(['-V'])
		match = re.match(r'^Yosys (\d+)\.(\d+)(?:\+(\d+))?', version)
		if match:
			return (int(match[1]), int(match[2]), int(match[3] or 0))
		else:
			return None

	@classmethod
	def data_dir(cls) -> Path:
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
		cls, args : List[str], stdin : str = '', *, ignore_warnings : bool = False, src_loc_at : int = 0
	) -> str:
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


def find_yosys(requirement : Callable[[Optional[Tuple[int, int, int]]], bool]) -> YosysBinary:
	'''Find an available Yosys executable of required version.

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
	proxies = []
	clauses = os.environ.get('TORII_USE_YOSYS', 'system,builtin').split(',')
	for clause in clauses:
		if clause == 'builtin':
			proxies.append(_BuiltinYosys)
		elif clause == 'system':
			proxies.append(_SystemYosys)
		else:
			raise YosysError(
				f'The TORII_USE_YOSYS environment variable contains an unrecognized clause {clause!r}'
			)
	for proxy in proxies:
		if proxy.available():
			version = proxy.version()
			if version is not None and requirement(version):
				return proxy
	else:
		if 'TORII_USE_YOSYS' in os.environ:
			raise YosysError(f'Could not find an acceptable Yosys binary. Searched: {", ".join(clauses)}')
		else:
			raise YosysError(
				'Could not find an acceptable Yosys binary. The `amaranth-yosys` PyPI '
				'package, if available for this platform, can be used as fallback'
			)
