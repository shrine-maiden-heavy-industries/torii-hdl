from torii.compat.sim import *
from torii.compat.sim import __all__


import warnings
warnings.warn("instead of nmigen.compat.sim, use torii.compat.sim",
              DeprecationWarning, stacklevel=2)
