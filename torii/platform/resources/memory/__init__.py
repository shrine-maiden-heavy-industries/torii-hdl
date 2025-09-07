# SPDX-License-Identifier: BSD-2-Clause

from typing        import Literal

from ....build.dsl import Attrs, DiffPairs, Pins, PinsN, Resource, ResourceConn, SubsigArgT, Subsignal


from .flash        import (
	NORFlashResources, QSPIDataMode, QSPIFlashResource, QSPIMode, SDCardResources, SPIFlashResources
)
from .ram          import DDR3Resource, SDRAMResource, SRAMResource

__all__ = (
	'DDR3Resource',
	'HyperBusResource',
	'NORFlashResources',
	'QSPIDataMode',
	'QSPIFlashResource',
	'QSPIMode',
	'SDCardResources',
	'SDRAMResource',
	'SPIFlashResources',
	'SRAMResource',
)

def HyperBusResource(
	name_or_number: str | int, number: int | None = None, *,
	bus_type: Literal['controller', 'peripheral'],
	cs_n: str, clk_p: str, clk_n: str | None, dq: str, rwds: str, rst_n: str | None = None,
	rsto_n: str | None = None, int_n: str | None = None,
	conn: ResourceConn | None = None, diff_attrs = None, attrs: Attrs | None = None,
):
	'''
	.. todo:: Document Me
	'''

	ios: list[SubsigArgT] = [
		Subsignal('cs', PinsN(cs_n, dir = 'o' if bus_type == 'controller' else 'i', conn = conn, assert_width = 1)),
		Subsignal('dq', Pins(dq, dir = 'io', conn = conn, assert_width = 8)),
		Subsignal('rwds', Pins(rwds, dir = 'io', conn = conn, assert_width = 1)),
	]

	if clk_n is None:
		ios.append(
			Subsignal('clk', Pins(
				clk_p, dir = 'o' if bus_type == 'controller' else 'i', conn = conn, assert_width = 1
			))
		)
	else:
		ios.append(
			Subsignal('clk', DiffPairs(
				clk_p, clk_n, dir = 'o' if bus_type == 'controller' else 'i', conn = conn, assert_width = 1
			), diff_attrs)
		)

	if rst_n is not None:
		ios.append(
			Subsignal('rst', PinsN(
				rst_n, dir = 'o' if bus_type == 'controller' else 'i', conn = conn, assert_width = 1
			))
		)

	if rsto_n is not None:
		ios.append(
			Subsignal('rsto', PinsN(
				rsto_n, dir = 'i' if bus_type == 'controller' else 'o', conn = conn, assert_width = 1
			))
		)

	if int_n is not None:
		ios.append(
			Subsignal('int', PinsN(
				int_n, dir = 'i' if bus_type == 'controller' else 'o', conn = conn, assert_width = 1
			))
		)

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'hyperbus', ios = ios)
