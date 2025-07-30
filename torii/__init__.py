# SPDX-License-Identifier: BSD-2-Clause
try:
	from importlib import metadata
	__version__ = metadata.version(__package__)
except ImportError: # :nocov:
	__version__ = 'unknown'

from .diagnostics.hooks import install_handlers

# Install the warning and excepthook handlers
install_handlers()

__all__ = ()
