# SPDX-License-Identifier: BSD-2-Clause

from .openlane import OpenLANEPlatform


__all__ = (
	'OpenLANEPlatform',
)

class EfablessCaravel(OpenLANEPlatform):

	def __init__(self) -> None:
		super().__init__()
