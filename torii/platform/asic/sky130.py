# SPDX-License-Identifier: BSD-3-Clause

from .openlane import OpenLANEPlatform

__all__ = (
	'SKY130_PLATFORMS',

	'SKY130A_PLATFORMS',
	'Sky130APlatform',
	'Sky130AHighDensityPlatform',
	'Sky130AHighSpeedPlatform',
	'Sky130AMediumSpeedPlatform',
	'Sky130ALowSpeedPlatform',
	'Sky130AHighDensityLowLeakagePlatform',

	'SKY130B_PLATFORMS',
	'Sky130BPlatform',
	'Sky130BHighDensityPlatform',
	'Sky130BHighSpeedPlatform',
	'Sky130BMediumSpeedPlatform',
	'Sky130BLowSpeedPlatform',
	'Sky130BHighDensityLowLeakagePlatform',

)

# PDK Key:
#  * FD - Foundry
#  * SC - Standard Cell
#  * HD - High Density
#  * HDLL - High Density Low Leakage
#  * LS/MS/HS - Low/Medium/High Speed

class Sky130APlatform(OpenLANEPlatform):
	'''OpenLANE - Sky130A PDK Platform

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This is the base platform the specifies the the sky130A PDK.

	Don't use this platform directly unless you plan to override behavior, use one
	of the specialized platforms instead:

	 * :py:class:`Sky130AHighDensityPlatform`
	 * :py:class:`Sky130AHighSpeedPlatform`
	 * :py:class:`Sky130AMediumSpeedPlatform`
	 * :py:class:`Sky130ALowSpeedPlatform`
	 * :py:class:`Sky130AHighDensityLowLeakagePlatform`

	''' # noqa: E101

	pdk = 'sky130A'

class Sky130AHighDensityPlatform(Sky130APlatform):
	'''OpenLANE - Sky130A High Density

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This platform is a specialization of the :py:class:`Sky130APlatform` that sets
	the cell library to ``sky130_fd_sc_hd`` for the high-density standard cells.

	'''
	cell_library = 'sky130_fd_sc_hd'

class Sky130AHighSpeedPlatform(Sky130APlatform):
	'''OpenLANE - Sky130A High Speed

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This platform is a specialization of the :py:class:`Sky130APlatform` that sets
	the cell library to ``sky130_fd_sc_hs`` for the high speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_hs'

class Sky130AMediumSpeedPlatform(Sky130APlatform):
	'''OpenLANE - Sky130A Medium Speed

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This platform is a specialization of the :py:class:`Sky130APlatform` that sets
	the cell library to ``sky130_fd_sc_ms`` for the medium speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_ms'

class Sky130ALowSpeedPlatform(Sky130APlatform):
	'''OpenLANE - Sky130A Low Speed

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This platform is a specialization of the :py:class:`Sky130APlatform` that sets
	the cell library to ``sky130_fd_sc_ls`` for the low speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_ls'

class Sky130AHighDensityLowLeakagePlatform(Sky130APlatform):
	'''OpenLANE - Sky130A High Density Low Leakage

	.. warning::

		**DO NOT** use any of the sky130A platforms unless you absolutely are sure
		you know what you're doing, use the sky130B platforms instead!

	This platform is a specialization of the :py:class:`Sky130APlatform` that sets
	the cell library to ``sky130_fd_sc_hdll`` for the high-density low-leakage standard cells.

	'''

	cell_library = 'sky130_fd_sc_hdll'

class Sky130BPlatform(OpenLANEPlatform):
	'''OpenLANE - Sky130B PDK Platform

	This is the base platform the specifies the the sky130A PDK.

	Don't use this platform directly unless you plan to override behavior, use one
	of the specialized platforms instead:

	 * :py:class:`Sky130BHighDensityPlatform`
	 * :py:class:`Sky130BHighSpeedPlatform`
	 * :py:class:`Sky130BMediumSpeedPlatform`
	 * :py:class:`Sky130BLowSpeedPlatform`
	 * :py:class:`Sky130BHighDensityLowLeakagePlatform`

	''' # noqa: E101

	pdk = 'sky130B'

class Sky130BHighDensityPlatform(Sky130BPlatform):
	'''OpenLANE - Sky130B High Density

	This platform is a specialization of the :py:class:`Sky130BPlatform` that sets
	the cell library to ``sky130_fd_sc_hd`` for the high-density standard cells.

	'''

	cell_library = 'sky130_fd_sc_hd'

class Sky130BHighSpeedPlatform(Sky130BPlatform):
	'''OpenLANE - Sky130B High Speed


	This platform is a specialization of the :py:class:`Sky130BPlatform` that sets
	the cell library to ``sky130_fd_sc_hs`` for the high speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_hs'

class Sky130BMediumSpeedPlatform(Sky130BPlatform):
	'''OpenLANE - Sky130B Medium Speed


	This platform is a specialization of the :py:class:`Sky130BPlatform` that sets
	the cell library to ``sky130_fd_sc_ms`` for the medium speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_ms'

class Sky130BLowSpeedPlatform(Sky130BPlatform):
	'''OpenLANE - Sky130B Low Speed


	This platform is a specialization of the :py:class:`Sky130BPlatform` that sets
	the cell library to ``sky130_fd_sc_ls`` for the low speed standard cells.

	'''

	cell_library = 'sky130_fd_sc_ls'

class Sky130BHighDensityLowLeakagePlatform(Sky130BPlatform):
	'''OpenLANE - Sky130B High Density Low Leakage

	This platform is a specialization of the :py:class:`Sky130BPlatform` that sets
	the cell library to ``sky130_fd_sc_hdll`` for the high-density low-leakage standard cells.

	'''

	cell_library = 'sky130_fd_sc_hdll'

SKY130A_PLATFORMS = {
	'sky130_fd_sc_hd'  : Sky130AHighDensityPlatform,
	'sky130_fd_sc_hs'  : Sky130AHighSpeedPlatform,
	'sky130_fd_sc_ms'  : Sky130AMediumSpeedPlatform,
	'sky130_fd_sc_ls'  : Sky130ALowSpeedPlatform,
	'sky130_fd_sc_hdll': Sky130AHighDensityLowLeakagePlatform,
}

SKY130B_PLATFORMS = {
	'sky130_fd_sc_hd'  : Sky130BHighDensityPlatform,
	'sky130_fd_sc_hs'  : Sky130BHighSpeedPlatform,
	'sky130_fd_sc_ms'  : Sky130BMediumSpeedPlatform,
	'sky130_fd_sc_ls'  : Sky130BLowSpeedPlatform,
	'sky130_fd_sc_hdll': Sky130BHighDensityLowLeakagePlatform,
}

SKY130_PLATFORMS = {
	'sky130A': SKY130A_PLATFORMS,
	'sky130B': SKY130B_PLATFORMS,
}
