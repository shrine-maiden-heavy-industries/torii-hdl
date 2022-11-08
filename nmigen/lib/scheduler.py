from torii.lib.scheduler import *
from torii.lib.scheduler import __all__


import warnings
warnings.warn("instead of nmigen.lib.scheduler, use torii.lib.scheduler",
              DeprecationWarning, stacklevel=2)
