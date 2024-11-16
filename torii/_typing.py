# SPDX-License-Identifier: BSD-2-Clause

from typing import TYPE_CHECKING
from typing import TypeAlias, Literal
from enum   import Enum

# Import any circular deps
if TYPE_CHECKING:
	pass

IODirection: TypeAlias      = Literal['i', 'o']
IODirectionIO: TypeAlias    = IODirection   | Literal['io']
IODirectionOE: TypeAlias    = IODirectionIO | Literal['oe']
IODirectionEmpty: TypeAlias = IODirectionOE | Literal['-']

SrcLoc = tuple[str, int]

CaseT: TypeAlias = str | int | Enum | None
SwitchCaseT: TypeAlias = CaseT | tuple[CaseT, ...]
