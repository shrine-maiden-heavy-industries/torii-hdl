from torii.sim.pysim import *
from torii.sim.pysim import __all__


import warnings
warnings.warn("instead of nmigen.sim.pysim, use torii.sim.pysim",
              DeprecationWarning, stacklevel=2)
