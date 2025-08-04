# SPDX-License-Identifier: BSD-2-Clause

from .bus     import DirectUSBResource, PCIBusResources, PCIeBusResources, ULPIResource
from .network import CANResource, EthernetResource
from .serial  import I2CResource, IrDAResource, JTAGResource, PS2Resource, SPIResource, UARTResource

__all__ = (
	'CANResource',
	'DirectUSBResource',
	'EthernetResource',
	'I2CResource',
	'IrDAResource',
	'JTAGResource',
	'PCIBusResources',
	'PCIeBusResources',
	'PS2Resource',
	'SPIResource',
	'UARTResource',
	'ULPIResource',
)
