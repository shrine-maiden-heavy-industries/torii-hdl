# SPDX-License-Identifier: BSD-2-Clause

from functools    import cache
from os           import environ
from pathlib      import Path
from typing       import Final

from platformdirs import PlatformDirs

from ..           import __version__

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
	ensure_exists = True # NOTE(aki): This will cause most if not all `get_sys_*` calls to explode by default
)
''' A pre-constructed :py:class:`PlatformDirs <platformdirs.PlatformDirs>` object for Torii '''

@cache
def get_sys_cache() -> Path:
	'''
	Returns the path to the system-wide cache directory.

	If the ``TORII_CACHE_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate system cache directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_CACHE_DIR', TORII_PLATFORM_DIRS.site_cache_dir)).resolve()

@cache
def get_sys_config() -> Path:
	'''
	Returns the path to the system-wide configuration directory.

	If the ``TORII_CONFIG_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate system configuration directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_CONFIG_DIR', TORII_PLATFORM_DIRS.site_config_dir)).resolve()

@cache
def get_sys_data() -> Path:
	'''
	Returns the path to the system-wide data directory.

	If the ``TORII_DATA_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate system data directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_DATA_DIR', TORII_PLATFORM_DIRS.site_data_dir)).resolve()

@cache
def get_sys_runtime() -> Path:
	'''
	Returns the path to the system-wide runtime directory.

	If the ``TORII_RUNTIME_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate system runtime directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_RUNTIME_DIR', TORII_PLATFORM_DIRS.site_runtime_dir)).resolve()

@cache
def get_user_cache() -> Path:
	'''
	Returns the path to the user-specific cache directory.

	If the ``TORII_CACHE_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate user cache directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_CACHE_DIR', TORII_PLATFORM_DIRS.user_cache_dir)).resolve()

@cache
def get_user_config() -> Path:
	'''
	Returns the path to the user-specific configuration directory.

	If the ``TORII_CONFIG_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate user configuration directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_CONFIG_DIR', TORII_PLATFORM_DIRS.user_config_dir)).resolve()

@cache
def get_user_data() -> Path:
	'''
	Returns the path to the user-specific data directory.

	If the ``TORII_DATA_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate user data directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_DATA_DIR', TORII_PLATFORM_DIRS.user_data_dir)).resolve()

@cache
def get_user_runtime() -> Path:
	'''
	Returns the path to the user-specific runtime directory.

	If the ``TORII_RUNTIME_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate user runtime directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_RUNTIME_DIR', TORII_PLATFORM_DIRS.user_runtime_dir)).resolve()

@cache
def get_user_state() -> Path:
	'''
	Returns the path to the user-specific state directory.

	If the ``TORII_STATE_DIR`` environment variable is set, that is used instead.

	Returns
	-------
	Path
		The path to the appropriate user state directory.

	Raises
	------
	PermissionError
		If we are unable to create the target directory if it doesn't exist.
	'''

	return Path(environ.get('TORII_STATE_DIR', TORII_PLATFORM_DIRS.user_state_dir)).resolve()
