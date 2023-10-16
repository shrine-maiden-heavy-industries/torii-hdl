# SPDX-License-Identifier: BSD-2-Clause

from .display    import Display7SegResource, VGADACResource, VGAResource
from .extensions import (
	PmodDualHBridgeType6Resource, PmodGPIOType1Resource,
	PmodHBridgeType5Resource, PmodSPIType2AResource,
	PmodSPIType2Resource, PmodUARTType3Resource,
	PmodUARTType4AResource, PmodUARTType4Resource
)
from .interface  import (
	CANResource, DirectUSBResource, I2CResource, IrDAResource,
	JTAGResource, PS2Resource, SPIResource, UARTResource,
	ULPIResource, HyperBusResource
)
from .memory     import (
	DDR3Resource, NORFlashResources, QSPIFlashResource,
	SDCardResources, SDRAMResource, SPIFlashResources,
	SRAMResource
)
from .user       import (
	ButtonResources, LEDResources, RGBLEDResource, SwitchResources
)

__all__ = (
	'Display7SegResource',
	'VGADACResource',
	'VGAResource',

	'PmodDualHBridgeType6Resource',
	'PmodGPIOType1Resource',
	'PmodHBridgeType5Resource',
	'PmodSPIType2AResource',
	'PmodSPIType2Resource',
	'PmodUARTType3Resource',
	'PmodUARTType4AResource',
	'PmodUARTType4Resource',

	'CANResource',
	'DirectUSBResource',
	'I2CResource',
	'IrDAResource',
	'JTAGResource',
	'PS2Resource',
	'SPIResource',
	'UARTResource',
	'ULPIResource',
	'HyperBusResource',

	'DDR3Resource',
	'NORFlashResources',
	'QSPIFlashResource',
	'SDCardResources',
	'SDRAMResource',
	'SPIFlashResources',
	'SRAMResource',

	'ButtonResources',
	'LEDResources',
	'RGBLEDResource',
	'SwitchResources',
)
