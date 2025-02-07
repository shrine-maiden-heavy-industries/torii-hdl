# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from enum       import Enum
from typing     import TYPE_CHECKING, Literal, TypeAlias

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
