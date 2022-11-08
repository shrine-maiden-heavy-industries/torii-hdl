from torii.build.run import *
from torii.build.run import __all__


import warnings
warnings.warn("instead of nmigen.build.run, use torii.build.run",
              DeprecationWarning, stacklevel=2)
