from torii.compat.genlib.fifo import *
from torii.compat.genlib.fifo import __all__


import warnings
warnings.warn("instead of nmigen.compat.genlib.fifo, use torii.compat.genlib.fifo",
              DeprecationWarning, stacklevel=2)
