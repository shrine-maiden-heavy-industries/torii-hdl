from torii.compat.fhdl.decorators import *
from torii.compat.fhdl.decorators import __all__


import warnings
warnings.warn("instead of nmigen.compat.fhdl.decorators, use torii.compat.fhdl.decorators",
              DeprecationWarning, stacklevel=2)
