from torii.compat.fhdl.module import *
from torii.compat.fhdl.module import __all__


import warnings
warnings.warn("instead of nmigen.compat.fhdl.module, use torii.compat.fhdl.module",
              DeprecationWarning, stacklevel=2)
