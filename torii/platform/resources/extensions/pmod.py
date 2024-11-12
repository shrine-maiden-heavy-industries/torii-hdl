# SPDX-License-Identifier: BSD-2-Clause
# Reference: https://www.digilentinc.com/Pmods/Digilent-Pmod_%20Interface_Specification.pdf

from ....build.dsl import Pins, PinsN, Resource, Subsignal, SubsigArgT

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
	return Resource(name, number, Pins('1 2 3 4', dir = 'io', conn = ('pmod', pmod)), *args)


def PmodSPIType2Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('cs',   PinsN('1', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('clk',   Pins('2', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('copi',  Pins('3', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('cipo',  Pins('4', dir = 'i', conn = ('pmod', pmod))),
		*args
	)


def PmodSPIType2AResource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('cs',   PinsN('1', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('clk',   Pins('2', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('copi',  Pins('3', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('cipo',  Pins('4', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('int',   Pins('7', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('reset', Pins('8', dir = 'o', conn = ('pmod', pmod))),
		*args
	)


def PmodUARTType3Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('rts',   Pins('2', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('tx',    Pins('4', dir = 'o', conn = ('pmod', pmod))),
		*args
	)


def PmodUARTType4Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('tx',    Pins('2', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('rts',   Pins('4', dir = 'o', conn = ('pmod', pmod))),
		*args
	)


def PmodUARTType4AResource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('cts',   Pins('1', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('tx',    Pins('2', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('rx',    Pins('3', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('rts',   Pins('4', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('int',   Pins('7', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('reset', Pins('8', dir = 'o', conn = ('pmod', pmod))),
		*args
	)


def PmodHBridgeType5Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('dir',   Pins('1', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('en',    Pins('2', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('sa',    Pins('3', dir = 'i', conn = ('pmod', pmod))),
		Subsignal('sb',    Pins('4', dir = 'i', conn = ('pmod', pmod))),
		*args
	)


def PmodDualHBridgeType6Resource(name: str, number: int, *args: SubsigArgT, pmod: int) -> Resource:
	return Resource(
		name, number,
		Subsignal('dir',   Pins('1 3', dir = 'o', conn = ('pmod', pmod))),
		Subsignal('en',    Pins('2 4', dir = 'o', conn = ('pmod', pmod))),
		*args
	)
