# SPDX-License-Identifier: BSD-2-Clause
try:
	from importlib import metadata
	__version__ = metadata.version(__package__)
except ImportError: # :nocov:
	__version__ = 'unknown'

from .diagnostics.hooks import install_handler

# Install the warnings handler
install_handler()

__all__ = ()
