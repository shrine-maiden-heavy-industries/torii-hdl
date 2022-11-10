# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil

__all__ = (
	'ToolNotFound',
	'tool_env_var',
	'has_tool',
	'require_tool',
)

class ToolNotFound(Exception):
	pass


def tool_env_var(name):
	return name.upper().replace('-', '_').replace('+', 'X')


def _get_tool(name):
	return os.environ.get(tool_env_var(name), name)


def has_tool(name):
	return shutil.which(_get_tool(name)) is not None


def require_tool(name):
	env_var = tool_env_var(name)
	path = _get_tool(name)
	if shutil.which(path) is None:
		if env_var in os.environ:
			raise ToolNotFound(f'Could not find required tool {name} in {path} as '
							   f'specified via the {env_var} environment variable')
		else:
			raise ToolNotFound(f'Could not find required tool {name} in PATH. Place '
							   'it directly in PATH or specify path explicitly '
							   f'via the {env_var} environment variable')
	return path
