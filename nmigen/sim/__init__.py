from torii.sim import *
from torii.sim import __all__


import warnings
warnings.warn("instead of nmigen.sim, use torii.sim",
              DeprecationWarning, stacklevel=2)
