# SPDX-License-Identifier: BSD-2-Clause

from .display    import Display7SegResource, VGADACResource, VGAResource
from .interface  import (
	UARTResource, ULPIResource, SPIResource, I2CResource, DirectUSBResource,
	PS2Resource, CANResource, JTAGResource
)
from .memory     import (
	SPIFlashResources, QSPIFlashResource, SDCardResources, SRAMResource,
	SDRAMResource, NORFlashResources, DDR3Resource
)
from .user       import LEDResources, RGBLEDResource, ButtonResources, SwitchResources
from .extensions import (
	PmodGPIOType1Resource, PmodSPIType2Resource, PmodSPIType2AResource, PmodUARTType3Resource,
	PmodUARTType4Resource, PmodUARTType4AResource, PmodHBridgeType5Resource,
	PmodDualHBridgeType6Resource,
)


__all__ = (
	'Display7SegResource',
	'VGAResource',
	'VGADACResource',
	'UARTResource',
	'IrDAResource',
	'SPIResource',
	'I2CResource',
	'DirectUSBResource',
	'ULPIResource',
	'PS2Resource',
	'CANResource',
	'JTAGResource',
	'SPIFlashResources',
	'SDCardResources',
	'SRAMResource',
	'SDRAMResource',
	'NORFlashResources',
	'QSPIFlashResource',
	'DDR3Resource',
	'LEDResources',
	'RGBLEDResource',
	'ButtonResources',
	'SwitchResources',

	'PmodGPIOType1Resource',
	'PmodSPIType2Resource',
	'PmodSPIType2AResource',
	'PmodUARTType3Resource',
	'PmodUARTType4Resource',
	'PmodUARTType4AResource',
	'PmodHBridgeType5Resource',
	'PmodDualHBridgeType6Resource',
)
