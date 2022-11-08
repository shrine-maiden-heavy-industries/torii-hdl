from torii.test.utils import *
from torii.test.utils import __all__


import warnings
warnings.warn("instead of nmigen.test.utils, use torii.test.utils",
              DeprecationWarning, stacklevel=2)
