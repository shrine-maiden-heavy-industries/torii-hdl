from torii.lib.fifo import *
from torii.lib.fifo import __all__


import warnings
warnings.warn("instead of nmigen.lib.fifo, use torii.lib.fifo",
              DeprecationWarning, stacklevel=2)
