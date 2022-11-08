from torii.sim.core import *
from torii.sim.core import __all__


import warnings
warnings.warn("instead of nmigen.sim.core, use torii.sim.core",
              DeprecationWarning, stacklevel=2)
