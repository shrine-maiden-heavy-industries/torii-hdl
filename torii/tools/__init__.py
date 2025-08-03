# SPDX-License-Identifier: BSD-2-Clause

from os            import environ
from shutil        import which

from ..            import diagnostics
from ..util.string import tool_env_var

__doc__ = '''\

.. warning:

	The following module is internal implementation details for Torii and should
	not be considered stable or for external use.

'''

__all__ = (
	'has_tool',
	'require_tool',
)

def __dir__() -> list[str]:
	return list({*__all__, 'ToolNotFound'})

def __getattr__(name: str):
	if name == 'ToolNotFound':
		from warnings import warn
		warn(
			f'The import of {name} from {__name__} has been deprecated and moved '
			f'to torii.diagnostics.{name}', DeprecationWarning, stacklevel = 2
		)
		return diagnostics.ToolNotFound
	raise AttributeError(f'Module {__name__!r} has no attribute {name!r}')

def _get_tool(name: str) -> str:
	'''
	Get the tool name or path if overridden by an environment variable.

	Parameters
	----------
	name : str
		The tool/executable name.

	Returns
	-------
	str
		The tool/executable name if not found in the environment.

	'''

	return environ.get(tool_env_var(name), name)

def has_tool(name: str) -> bool:
	'''
	Check to see if the tool or executable is in the current PATH.

	Parameters
	----------
	name : str
		The tool/executable name.

	Returns
	-------
	bool
		If the tool/executable was found in the current system PATH.

	'''

	return which(_get_tool(name)) is not None

def require_tool(name: str) -> str:
	'''
	Return the fully resolved path to the requested tool or executable
	if found, otherwise throw a ToolNotFound exception.

	Parameters
	----------
	name : str
		The tool/executable name.

	Returns
	-------
	Path
		The fully qualified path to the executable / tool.

	Raises
	------
	ToolNotFound

	'''
	env_var = tool_env_var(name)
	path = _get_tool(name)
	if which(path) is None:
		if env_var in environ:
			raise diagnostics.ToolNotFound(
				f'Could not find required tool {name} in {path} as specified via '
				f'the {env_var} environment variable'
			)
		else:
			raise diagnostics.ToolNotFound(
				f'Could not find required tool {name} in PATH. Place '
				'it directly in PATH or specify path explicitly '
				f'via the {env_var} environment variable'
			)
	return path
