# SPDX-License-Identifier: BSD-2-Clause

from .dsl                 import Attrs, Clock, Connector, DiffPairs, DiffPairsN, Pins, PinsN, Resource, Subsignal
from .plat                import PinFeature, Platform, TemplatedPlatform
from ..diagnostics.errors import ResourceError

__all__ = (
	'Attrs',
	'Clock',
	'Connector',
	'DiffPairs',
	'DiffPairsN',
	'Pins',
	'PinsN',
	'PinFeature',
	'Platform',
	'Resource',
	'ResourceError',
	'Subsignal',
	'TemplatedPlatform',
)
