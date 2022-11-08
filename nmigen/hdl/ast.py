from torii.hdl.ast import *
from torii.hdl.ast import __all__


import warnings
warnings.warn("instead of nmigen.hdl.ast, use torii.hdl.ast",
              DeprecationWarning, stacklevel=2)
