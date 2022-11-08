from torii.back.pysim import *
from torii.back.pysim import __all__


import warnings
warnings.warn("instead of nmigen.back.pysim, use torii.back.pysim",
              DeprecationWarning, stacklevel=2)
