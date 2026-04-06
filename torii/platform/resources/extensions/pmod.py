# SPDX-License-Identifier: BSD-2-Clause
# Reference: https://web.archive.org/web/20260319171338/https://digilent.com/reference/_media/reference/pmod/pmod-interface-specification-1_3_1.pdf # noqa: E501

from ....build.dsl import Pins, PinsN, Resource, SubsigArgT, Subsignal

__all__ = (
	'PmodDualHBridgeType6Resource',
	'PmodGPIOType1Resource',
	'PmodHBridgeType5Resource',
	'PmodSPIType2AResource',
	'PmodSPIType2Resource',
	'PmodUARTType3Resource',
	'PmodUARTType4AResource',
	'PmodUARTType4Resource',
)

def PmodGPIOType1Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number, Pins('1 2 3 4', dir = 'io', conn = ('pmod', pmod), src_loc_at = 1), *args, src_loc_at = 1
	)

def PmodSPIType2Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('cs',   PinsN('1', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('clk',   Pins('2', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('copi',  Pins('3', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('cipo',  Pins('4', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodSPIType2AResource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('cs',   PinsN('1', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('clk',   Pins('2', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('copi',  Pins('3', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('cipo',  Pins('4', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('int',   Pins('7', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('reset', Pins('8', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodUARTType3Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rts',   Pins('2', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('tx',    Pins('4', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodUARTType4Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('tx',    Pins('2', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rts',   Pins('4', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodUARTType4AResource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('tx',    Pins('2', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('rts',   Pins('4', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('int',   Pins('7', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('reset', Pins('8', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodHBridgeType5Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('dir',   Pins('1', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('en',    Pins('2', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('sa',    Pins('3', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('sb',    Pins('4', dir = 'i', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)

def PmodDualHBridgeType6Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	'''
	.. todo:: Document Me
	'''

	return Resource(
		name, number,
		Subsignal('dir',   Pins('1 3', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		Subsignal('en',    Pins('2 4', dir = 'o', conn = ('pmod', pmod), src_loc_at = 1), src_loc_at = 1),
		*args,
		src_loc_at = 1
	)
