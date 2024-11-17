# SPDX-License-Identifier: BSD-2-Clause

import hashlib
import os
import subprocess
import sys
import zipfile
import tarfile

from abc             import ABCMeta, abstractmethod
from collections     import OrderedDict
from collections.abc import Generator
from contextlib      import contextmanager
from pathlib         import Path
from typing          import Literal
from tempfile        import NamedTemporaryFile, _TemporaryFileWrapper

__all__ = (
	'BuildPlan',
	'BuildProducts',
	'LocalBuildProducts',
)

class BuildPlan:
	def __init__(self, script: str) -> None:
		'''
		A build plan.

		Parameters
		----------
		script : str
			The base name (without extension) of the script that will be executed.

		'''
		self.script = script
		self.files  = OrderedDict[str, str | bytes]()

	def add_file(self, filename: str, content: str | bytes) -> None:
		'''
		Add ``content``, which can be a :class:`str`` or :class:`bytes`, to the build plan
		as ``filename``. The file name can be a relative path with directories separated by
		forward slashes (``/``).
		'''
		if not isinstance(filename, str) or filename in self.files:
			raise ValueError('filename must be a string and must not already exist inside the file set already!')

		if Path(filename).is_absolute():
			raise ValueError(f'Filename {filename} must not be an absolute path')

		self.files[filename] = content

	def digest(self, size: int = 64) -> bytes:
		'''
		Compute a `digest`, a short byte sequence deterministically and uniquely identifying
		this build plan.
		'''
		hasher = hashlib.blake2b(digest_size = size)
		for filename in sorted(self.files):
			hasher.update(filename.encode('utf-8'))
			content = self.files[filename]
			if isinstance(content, str):
				content = content.encode('utf-8')
			hasher.update(content)
		hasher.update(self.script.encode('utf-8'))
		return hasher.digest()

	def archive(self, file: str | Path, archive_type: Literal['tar', 'zip'] = 'zip') -> None:
		'''
		Create an archive containing the results from the BuildPlan.

		Parameters
		----------
		file : str | Path
			The archive file path to write to.

		archive_type : 'tar' | 'zip'
			The type of archive to produce.

		'''
		_archive_types = {
			'zip': (zipfile.ZipFile, zipfile.ZipInfo, 'w',    '.zip'   ),
			'tar': (tarfile.TarFile, tarfile.TarInfo, 'w:xz', '.tar.xz')
		}

		if archive_type not in ('tar', 'zip'):
			raise ValueError(f'Archive type must be either \'tar\' or \'zip\' not {archive_type!r}')

		arch_t, archinfo_t, arch_mode, arch_ext = _archive_types.get(archive_type) # type: ignore

		if isinstance(file, str):
			file = Path(file)

		with arch_t(file.with_suffix(arch_ext), arch_mode) as archive:
			# Write archive members in deterministic order and with deterministic timestamp.
			for filename in sorted(self.files):
				archive.writestr(archinfo_t(filename), self.files[filename])

	def extract(self, root: str | Path = 'build') -> Path:
		'''
		Extracts the build plan files into the specified local build
		root.

		Returns
		-------
			:class:`pathlib.Path`
		'''

		if isinstance(root, str):
			root = Path(root).resolve()

		root.mkdir(parents = True, exist_ok = True)

		cwd = Path.cwd()
		try:
			os.chdir(root)

			for filename, content in self.files.items():
				file = Path(filename)
				# Forbid parent directory components and absolute paths completely
				# to avoid the possibility of writing outside the build root.
				if '..' in file.parts or file.is_absolute():
					raise RuntimeError(
						f'Unable to write to \'{file}\'\n'
						'Writing to outside of the build root is forbidden.'
					)

				file.parent.mkdir(parents = True, exist_ok = True)

				if isinstance(content, str):
					content = content.encode('utf-8')

				with file.resolve().open('wb') as f:
					f.write(content)

				# If we're on unix-like and we're emitting the shell script, set it as +x
				if not sys.platform.startswith('win32') and file.suffix == '.sh':
					file.chmod(0o755) # rwxr-xr-x
			return root
		finally:
			os.chdir(cwd)

	def execute_local(
		self, root: str | Path = 'build', *, env: dict[str, str] | None = None
	) -> 'LocalBuildProducts':
		'''
		Execute build plan using the local strategy. Files from the build plan are placed in
		the build root directory ``root``, and the script appropriate for the platform
		(``{script}.bat`` on Windows, ``{script}.sh`` elsewhere) is executed in the build root.

		If ``env`` is not ``None``, the environment is extended (not replaced) with ``env``.

		Returns :class:`LocalBuildProducts`.
		'''

		build_dir = self.extract(root)
		script_env = dict(os.environ)
		if env is not None:
			script_env.update(env)
		if sys.platform.startswith('win32'):
			# Without "call", "cmd /c {}.bat" will return 0.
			# See https://stackoverflow.com/a/30736987 for a detailed explanation of why.
			# Running the script manually from a command prompt is unaffected.
			subprocess.check_call(
				[ 'cmd', '/c', f'call {self.script}.bat' ],
				env = script_env,
				cwd = build_dir
			)
		else:
			subprocess.check_call(
				[ 'sh', f'{self.script}.sh' ],
				env = script_env,
				cwd = build_dir
			)

		return LocalBuildProducts(build_dir)

	def execute(self) -> 'LocalBuildProducts':
		'''
		Execute build plan using the default strategy. Use one of the ``execute_*`` methods
		explicitly to have more control over the strategy.
		'''
		return self.execute_local()

	def execute_docker(
		self, image: str, root: str | Path = 'root', docker_mount: str = '/build', docker_args: list[str] = []
	) -> 'LocalBuildProducts':
		'''

		Execute a build plan inside a Docker container.

		The build root is mounted into the container under ``docker_mount``
		and then the build script is ran in the container.

		Additional arguments to docker may be supplied with ``docker_args``.

		Parameters
		----------
		image : str
			The docker container image to use

		root : str | Path
			The Torii build root.

		docker_mount : str
			The internal docker bind mount location for the build root. (default: /build)

		docker_args : list[str]
			Any additional arguments to pass to the docker engine.

		Returns
		-------
			:class:`LocalBuildProducts`
		'''
		build_dir = self.extract(root)

		subprocess.check_call([
			'docker', 'run', *docker_args,
			'--rm', '-v', f'"{build_dir}":{docker_mount}',
			'--workdir', f'{docker_mount}',
			image,
			'sh', f'{self.script}.sh'
		])

		return LocalBuildProducts(build_dir)


class BuildProducts(metaclass = ABCMeta):
	@abstractmethod
	def get_str(self, filename: str) -> str:
		'''
		Get the contents of ``filename`` from the build products as a string.

		Parameters
		----------
		filename: str
			The name of the file to extract from the build products.

		Returns
		-------
		str
			The contents of ``filename`` as a UTF-8 encoded string.

		'''
		raise NotImplementedError()

	@abstractmethod
	def get_bin(self, filename: str) -> bytes:
		'''
		Get the contents of ``filename`` from the build products as raw bytes.

		Parameters
		----------
		filename: str
			The name of the file to extract from the build products.

		Returns
		-------
		bytes
			The contents of ``filename`` as raw bytes.

		'''
		raise NotImplementedError()

	@abstractmethod
	def get(self, filename: str, mode: Literal['b', 't'] = 'b') -> str | bytes:
		'''
		Extract ``filename`` from build products, and return it as a :class:`bytes` (if ``mode``
		is ``"b"``) or a :class:`str` (if ``mode`` is ``"t"``).
		'''
		raise NotImplementedError()


	@contextmanager
	def extract(self, *filenames: str) -> Generator[str | list[str] | None]:
		'''
		Extract ``filenames`` from build products, place them in an OS-specific temporary file
		location, with the extension preserved, and delete them afterwards. This method is used
		as a context manager, e.g.: ::

			with products.extract("bitstream.bin", "programmer.cfg") \
					as bitstream_filename, config_filename:
				subprocess.check_call(["program", "-c", config_filename, bitstream_filename])
		'''
		files: list[_TemporaryFileWrapper[bytes]] = []
		try:
			for filename in filenames:
				# On Windows, a named temporary file (as created by Python) is not accessible to
				# others if it's still open within the Python process, so we close it and delete
				# it manually.
				file = NamedTemporaryFile(
					prefix = 'torii_', suffix = '_' + os.path.basename(filename),
					delete = False)
				files.append(file)
				file.write(self.get_bin(filename))
				file.close()

			if len(files) == 0:
				return (yield None)
			elif len(files) == 1:
				return (yield files[0].name)
			else:
				return (yield [file.name for file in files])
		finally:
			for file in files:
				os.unlink(file.name)


class LocalBuildProducts(BuildProducts):
	def __init__(self, root: str | Path) -> None:
		# We provide no guarantees that files will be available on the local filesystem (i.e. in
		# any way other than through `products.get()`) in general, so downstream code must never
		# rely on this, even when we happen to use a local build most of the time.
		if isinstance(root, str):
			self.__root = Path(root)
		else:
			self.__root = root

	def get_str(self, filename: str) -> str:
		with (self.__root / filename).resolve().open('rt') as f:
			return f.read()


	def get_bin(self, filename: str) -> bytes:
		with (self.__root / filename).resolve().open('rb') as f:
			return f.read()

	def get(self, filename: str, mode: Literal['b', 't'] = 'b') -> str | bytes:
		match mode:
			case 'b':
				return self.get_bin(filename)
			case 't':
				return self.get_str(filename)
			case _:
				raise ValueError(f'Unsupported file access mode \'{mode}\', must be either \'b\' or \'t\'.')
