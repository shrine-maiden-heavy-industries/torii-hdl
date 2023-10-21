# SPDX-License-Identifier: BSD-2-Clause
from typing import (
	Literal, Optional, Union, Generator, Iterator, Callable,
	TypeVar, TYPE_CHECKING
)

if TYPE_CHECKING:
	pass


IODirection    = Literal['i', 'o', 'io']
IODirWithOE    = Literal['i', 'o', 'io', 'oe']
IODirWithEmpty = Literal['i', 'o', 'io', 'oe', '-']
