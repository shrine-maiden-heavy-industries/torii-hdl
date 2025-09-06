# SPDX-License-Identifier: BSD-2-Clause

from functools    import cache
from os           import environ
from pathlib      import Path
from typing       import Final
from warnings     import warn

from platformdirs import PlatformDirs

__all__ = (
	'TORII_PLATFORM_DIRS',
	'get_sys_cache',
	'get_sys_config',
	'get_sys_data',
	'get_sys_runtime',
	'get_user_cache',
	'get_user_config',
	'get_user_data',
	'get_user_runtime',
	'get_user_state',
)

TORII_PLATFORM_DIRS: Final[PlatformDirs] = PlatformDirs(
	appname = 'Torii',
	appauthor = 'Shrine Maiden Heavy Industries',
	roaming = True, # XXX(aki): Windows-only
	ensure_exists = False, # NOTE(aki): We fall-back to user dirs if we can make the sys-dir
)
''' A pre-constructed :py:class:`PlatformDirs <platformdirs.api.PlatformDirsABC>` object for Torii '''

@cache
def get_sys_cache(mkdir: bool = True) -> Path:
	'''
	Returns the path to the system-wide cache directory.

	If the ``TORII_CACHE_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate system cache directory if it exists, otherwise the user cache dir.

	Raises
	------
	PermissionError
		When the system directory doesn't exist, and we fall back to the user directory, if it doesn't exist
		and we can't create it.
	'''

	sys_cache_dir = Path(environ.get('TORII_CACHE_DIR', TORII_PLATFORM_DIRS.site_cache_dir)).resolve()
	try:
		if mkdir:
			sys_cache_dir.mkdir(parents = True, exist_ok = True)
		return sys_cache_dir
	except PermissionError:
		warn(
			f'The system cache dir for torii \'{sys_cache_dir}\' does not exist, falling back to user cache dir.',
			RuntimeWarning, stacklevel = 2
		)
		return get_user_cache(mkdir)

@cache
def get_sys_config(mkdir: bool = True) -> Path:
	'''
	Returns the path to the system-wide configuration directory.

	If the ``TORII_CONFIG_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate system configuration directory if it exists, otherwise the user config dir.

	Raises
	------
	PermissionError
		When the system directory doesn't exist, and we fall back to the user directory, if it doesn't exist
		and we can't create it.
	'''

	sys_config_dir = Path(environ.get('TORII_CONFIG_DIR', TORII_PLATFORM_DIRS.site_config_dir)).resolve()
	try:
		if mkdir:
			sys_config_dir.mkdir(parents = True, exist_ok = True)
		return sys_config_dir
	except PermissionError:
		warn(
			f'The system config dir for torii \'{sys_config_dir}\' does not exist, falling back to user config dir.',
			RuntimeWarning, stacklevel = 2
		)
		return get_user_config(mkdir)

@cache
def get_sys_data(mkdir: bool = True) -> Path:
	'''
	Returns the path to the system-wide data directory.

	If the ``TORII_DATA_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate system data directory if it exists, otherwise the user data dir.

	Raises
	------
	PermissionError
		When the system directory doesn't exist, and we fall back to the user directory, if it doesn't exist
		and we can't create it.
	'''

	sys_data_dir = Path(environ.get('TORII_DATA_DIR', TORII_PLATFORM_DIRS.site_data_dir)).resolve()
	try:
		if mkdir:
			sys_data_dir.mkdir(parents = True, exist_ok = True)
		return sys_data_dir
	except PermissionError:
		warn(
			f'The system config dir for torii \'{sys_data_dir}\' does not exist, falling back to user data dir.',
			RuntimeWarning, stacklevel = 2
		)
		return get_user_data(mkdir)

@cache
def get_sys_runtime(mkdir: bool = True) -> Path:
	'''
	Returns the path to the system-wide runtime directory.

	If the ``TORII_RUNTIME_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate system runtime directory if it exists, other wise the user runtime dir.

	Raises
	------
	PermissionError
		When the system directory doesn't exist, and we fall back to the user directory, if it doesn't exist
		and we can't create it.
	'''

	sys_runtime_dir = Path(environ.get('TORII_RUNTIME_DIR', TORII_PLATFORM_DIRS.site_runtime_dir)).resolve()
	try:
		if mkdir:
			sys_runtime_dir.mkdir(parents = True, exist_ok = True)
		return sys_runtime_dir
	except PermissionError:
		warn(
			f'The system config dir for torii \'{sys_runtime_dir}\' does not exist, falling back to user data dir.',
			RuntimeWarning, stacklevel = 2
		)
		return get_user_runtime(mkdir)

@cache
def get_user_cache(mkdir: bool = True) -> Path:
	'''
	Returns the path to the user-specific cache directory.

	If the ``TORII_CACHE_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate user cache directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	user_cache_dir = Path(environ.get('TORII_CACHE_DIR', TORII_PLATFORM_DIRS.user_cache_dir)).resolve()
	if mkdir:
		user_cache_dir.mkdir(parents = True, exist_ok = True)
	return user_cache_dir

@cache
def get_user_config(mkdir: bool = True) -> Path:
	'''
	Returns the path to the user-specific configuration directory.

	If the ``TORII_CONFIG_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate user configuration directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	user_config_dir = Path(environ.get('TORII_CONFIG_DIR', TORII_PLATFORM_DIRS.user_config_dir)).resolve()
	if mkdir:
		user_config_dir.mkdir(parents = True, exist_ok = True)
	return user_config_dir

@cache
def get_user_data(mkdir: bool = True) -> Path:
	'''
	Returns the path to the user-specific data directory.

	If the ``TORII_DATA_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate user data directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	user_data_dir = Path(environ.get('TORII_DATA_DIR', TORII_PLATFORM_DIRS.user_data_dir)).resolve()
	if mkdir:
		user_data_dir.mkdir(parents = True, exist_ok = True)
	return user_data_dir

@cache
def get_user_runtime(mkdir: bool = True) -> Path:
	'''
	Returns the path to the user-specific runtime directory.

	If the ``TORII_RUNTIME_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate user runtime directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	user_runtime_dir = Path(environ.get('TORII_RUNTIME_DIR', TORII_PLATFORM_DIRS.user_runtime_dir)).resolve()
	if mkdir:
		user_runtime_dir.mkdir(parents = True, exist_ok = True)
	return user_runtime_dir

@cache
def get_user_state(mkdir: bool = True) -> Path:
	'''
	Returns the path to the user-specific state directory.

	If the ``TORII_STATE_DIR`` environment variable is set, that is used instead.

	Parameters
	----------
	mkdir: bool
		Create the target directory if it doesn't exist.

	Returns
	-------
	Path
		The path to the appropriate user state directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	user_state_dir = Path(environ.get('TORII_STATE_DIR', TORII_PLATFORM_DIRS.user_state_dir)).resolve()
	if mkdir:
		user_state_dir.mkdir(parents = True, exist_ok = True)
	return user_state_dir
