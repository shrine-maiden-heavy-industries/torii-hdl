# SPDX-License-Identifier: BSD-2-Clause

from contextlib      import contextmanager
from os              import chdir
from pathlib         import Path
from collections.abc import Generator

__all__ = (
	'working_dir',
)

@contextmanager
def working_dir(new_cwd: str | Path) -> Generator[Path, None, None]:
	'''
	A context manager to change to the given working directory to do a task and then
	return to the previous working directory upon exit.

	Parameters
	----------
	new_cwd : str | PathLike
		The working directory to switch into.

	Raises
	------
	FileNotFoundError
		If the path given by ``new_cwd`` does not exist.

	'''

	cwd = Path.cwd()
	chdir(new_cwd)
	try:
		yield Path(new_cwd)
	finally:
		chdir(cwd)
