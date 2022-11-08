from torii.build.dsl import *
from torii.build.dsl import __all__


import warnings
warnings.warn("instead of nmigen.build.dsl, use torii.build.dsl",
              DeprecationWarning, stacklevel=2)
