from torii.hdl.mem import *
from torii.hdl.mem import __all__


import warnings
warnings.warn("instead of nmigen.hdl.mem, use torii.hdl.mem",
              DeprecationWarning, stacklevel=2)
