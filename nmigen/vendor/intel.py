from torii.vendor.intel import *
from torii.vendor.intel import __all__


import warnings
warnings.warn("instead of nmigen.vendor.intel, use torii.vendor.intel",
              DeprecationWarning, stacklevel=2)
