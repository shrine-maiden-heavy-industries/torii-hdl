from torii.compat.fhdl.specials import *
from torii.compat.fhdl.specials import __all__


import warnings
warnings.warn("instead of nmigen.compat.fhdl.specials, use torii.compat.fhdl.specials",
              DeprecationWarning, stacklevel=2)
