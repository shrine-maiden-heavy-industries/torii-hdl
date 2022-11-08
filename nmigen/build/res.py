from torii.build.res import *
from torii.build.res import __all__


import warnings
warnings.warn("instead of nmigen.build.res, use torii.build.res",
              DeprecationWarning, stacklevel=2)
