# SPDX-License-Identifier: BSD-2-Clause

from .dsl  import *
from .res  import ResourceError
from .plat import Platform, TemplatedPlatform

__all__ = (
	'Pins',
	'PinsN',
	'DiffPairs',
	'DiffPairsN',
	'Attrs',
	'Clock',
	'Subsignal',
	'Resource',
	'Connector',
	'ResourceError',
	'Platform', 'TemplatedPlatform',
)
