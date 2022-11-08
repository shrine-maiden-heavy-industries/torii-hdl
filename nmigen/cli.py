from torii.cli import main, main_parser, main_runner
from torii.cli import __all__


import warnings
warnings.warn("instead of nmigen.cli, use torii.cli",
              DeprecationWarning, stacklevel=2)
