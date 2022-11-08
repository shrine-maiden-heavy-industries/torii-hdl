from torii.hdl.dsl import *
from torii.hdl.dsl import __all__


import warnings
warnings.warn("instead of nmigen.hdl.dsl, use torii.hdl.dsl",
              DeprecationWarning, stacklevel=2)
