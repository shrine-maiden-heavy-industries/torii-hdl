from torii.back.verilog import *
from torii.back.verilog import __all__


import warnings
warnings.warn("instead of nmigen.back.verilog, use torii.back.verilog",
              DeprecationWarning, stacklevel=2)
