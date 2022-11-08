from torii.lib.io import *
from torii.lib.io import __all__


import warnings
warnings.warn("instead of nmigen.lib.io, use torii.lib.io",
              DeprecationWarning, stacklevel=2)
