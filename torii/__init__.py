# SPDX-License-Identifier: BSD-2-Clause

from importlib          import metadata
from typing             import Final

from .diagnostics.hooks import install_handlers

__version__: Final = metadata.version(__spec__.parent)

# Install the warning and excepthook handlers
install_handlers()

__all__ = ()
