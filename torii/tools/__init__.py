# SPDX-License-Identifier: BSD-2-Clause

'''
Warning
-------
The following module is internal implementation details for Torii and should
not be considered stable or for external use.
'''

from os            import environ
from shutil        import which

from ..diagnostics import ToolNotFound
from ..util.string import tool_env_var

__all__ = (
	'has_tool',
	'require_tool',
)

def _get_tool(name: str) -> str:
	'''
	Get the tool name or path if overridden by an environment variable.

	The name for the environment variable to look at is computed by the
	:py:func:`tool_env_var <torii.util.string.tool_env_var>` function.

	If the environment variable is not set, then ``name`` is returned as-is.

	Parameters
	----------
	name: str
		The tool/executable name.

	Returns
	-------
	str
		The value of the environment variable for the tool if found, otherwise ``name``.
	'''

	return environ.get(tool_env_var(name), name)

def has_tool(name: str) -> bool:
	'''
	Check to see if the tool or executable is available.

	This method follows the same logic as :py:func:`require_tool` when doing the
	lookup for the tool itself, the only difference is no exceptions are thrown if
	the tool is not found.

	Parameters
	----------
	name: str
		The tool/executable name.

	Returns
	-------
	bool
		If the tool/executable was found in the current system ``PATH``.
	'''

	return which(_get_tool(name)) is not None

# TODO(aki): Should this return a `pathlib.Path`?
def require_tool(name: str) -> str:
	'''
	Return the fully resolved path to the requested tool or executable
	if found, otherwise throw a ToolNotFound exception.

	The logic for this check is as follows:

	* Compute expected environment variable name via :py:func:`tool_env_var <torii.util.string.tool_env_var>`
	* Check to see if the environment variable is set, if so, use that value, otherwise use ``name``
	* Use :py:func:`which <shutil.which>` to search the system ``PATH`` for the tool

	If the tool is found, return the resulting path, otherwise raise an error.

	Parameters
	----------
	name: str
		The name of the tool/executable.

	Returns
	-------
	str
		The fully qualified path to the tool/executable.

	Raises
	------
	torii.diagnostics.ToolNotFound
		If we are unable to locate the requested tool.
	'''

	# TODO(aki):  We do the env-var calculation twice here (once in _get_tool), do we need to?
	env_var = tool_env_var(name)
	path = _get_tool(name)
	if which(path) is None:
		if env_var in environ:
			raise ToolNotFound(
				f'Could not find required tool {name} in {path} as specified via '
				f'the {env_var} environment variable'
			)
		else:
			raise ToolNotFound(
				f'Could not find required tool {name} in PATH. Place '
				'it directly in PATH or specify path explicitly '
				f'via the {env_var} environment variable'
			)
	return path
