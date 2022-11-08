from torii.rpc import *
from torii.rpc import __all__


import warnings
warnings.warn("instead of nmigen.rpc, use torii.rpc",
              DeprecationWarning, stacklevel=2)
