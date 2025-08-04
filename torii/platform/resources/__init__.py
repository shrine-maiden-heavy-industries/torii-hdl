# SPDX-License-Identifier: BSD-2-Clause

from .display    import Display7SegResource, HDMIResource, VGADACResource, VGAResource
from .extensions import (
	PmodDualHBridgeType6Resource, PmodGPIOType1Resource, PmodHBridgeType5Resource, PmodSPIType2AResource,
	PmodSPIType2Resource, PmodUARTType3Resource, PmodUARTType4AResource, PmodUARTType4Resource,
)
from .interface  import (
	CANResource, DirectUSBResource, EthernetResource, I2CResource, IrDAResource, JTAGResource, PCIBusResources,
	PCIeBusResources, PS2Resource, SPIResource, UARTResource, ULPIResource,
)
from .memory     import (
	DDR3Resource, HyperBusResource, NORFlashResources, QSPIFlashResource, SDCardResources, SDRAMResource,
	SPIFlashResources, SRAMResource,
)
from .user       import ButtonResources, LEDResources, RGBLEDResource, SwitchResources

__all__ = (
	'ButtonResources',
	'CANResource',
	'DDR3Resource',
	'DirectUSBResource',
	'Display7SegResource',
	'EthernetResource',
	'HDMIResource',
	'HyperBusResource',
	'I2CResource',
	'IrDAResource',
	'JTAGResource',
	'LEDResources',
	'NORFlashResources',
	'PCIBusResources',
	'PCIeBusResources',
	'PmodDualHBridgeType6Resource',
	'PmodGPIOType1Resource',
	'PmodHBridgeType5Resource',
	'PmodSPIType2AResource',
	'PmodSPIType2Resource',
	'PmodUARTType3Resource',
	'PmodUARTType4AResource',
	'PmodUARTType4Resource',
	'PS2Resource',
	'QSPIFlashResource',
	'RGBLEDResource',
	'SDCardResources',
	'SDRAMResource',
	'SPIFlashResources',
	'SPIResource',
	'SRAMResource',
	'SwitchResources',
	'UARTResource',
	'ULPIResource',
	'VGADACResource',
	'VGAResource',
)
