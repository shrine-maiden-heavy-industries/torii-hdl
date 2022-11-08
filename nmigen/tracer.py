from torii.tracer import *
from torii.tracer import __all__


import warnings
warnings.warn("instead of nmigen.tracer, use torii.tracer",
              DeprecationWarning, stacklevel=2)
