from torii.build.plat import *
from torii.build.plat import __all__


import warnings
warnings.warn("instead of nmigen.build.plat, use torii.build.plat",
              DeprecationWarning, stacklevel=2)
