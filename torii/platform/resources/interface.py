# SPDX-License-Identifier: BSD-2-Clause

from typing       import TYPE_CHECKING, Literal
from warnings     import warn

from ..._typing   import IODirection
from ...build.dsl import Attrs, Clock, DiffPairs, Pins, PinsN, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'CANResource',
	'DirectUSBResource',
	'HyperBusResource',
	'I2CResource',
	'IrDAResource',
	'JTAGResource',
	'PCIeBusResources',
	'PS2Resource',
	'SPIResource',
	'UARTResource',
	'ULPIResource',
)

def UARTResource(
	name_or_number: str | int, number: int | None = None, *,
	rx: str, tx: str, rts: str | None = None, cts: str | None = None,
	dtr: str | None = None, dsr: str | None = None, dcd: str | None = None,
	ri: str | None = None, conn: ResourceConn | None = None,
	attrs: Attrs | None = None, role: str | None  = None
) -> Resource:

	if any(line is not None for line in (rts, cts, dtr, dsr, dcd, ri)):
		if role not in ('dce', 'dte'):
			raise ValueError(f'Invalid role, expected \'dce\' or \'dte\', not \'{role}\'')

	if role == 'dte':
		dce_to_dte = 'i'
		dte_to_dce = 'o'
	else:
		dce_to_dte = 'o'
		dte_to_dce = 'i'

	io: list[SubsigArgT] = []

	io.append(Subsignal('rx', Pins(rx, dir = 'i', conn = conn, assert_width = 1)))
	io.append(Subsignal('tx', Pins(tx, dir = 'o', conn = conn, assert_width = 1)))

	# NOTE(aki): The mess of `# type: ignore` below is because the dte/dce
	# 　　　　　　　role determination is hard to see through for mypy

	if rts is not None:
		io.append(Subsignal('rts', Pins(rts, dir = dte_to_dce, conn = conn, assert_width = 1))) # type: ignore

	if cts is not None:
		io.append(Subsignal('cts', Pins(cts, dir = dce_to_dte, conn = conn, assert_width = 1))) # type: ignore

	if dtr is not None:
		io.append(Subsignal('dtr', Pins(dtr, dir = dte_to_dce, conn = conn, assert_width = 1))) # type: ignore

	if dsr is not None:
		io.append(Subsignal('dsr', Pins(dsr, dir = dce_to_dte, conn = conn, assert_width = 1))) # type: ignore

	if dcd is not None:
		io.append(Subsignal('dcd', Pins(dcd, dir = dce_to_dte, conn = conn, assert_width = 1))) # type: ignore

	if ri is not None:
		io.append(Subsignal('ri', Pins(ri, dir = dce_to_dte, conn = conn, assert_width = 1))) # type: ignore

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'uart', ios = io)

def IrDAResource(
	number: int, *,
	rx: str, tx: str, en: str | None = None, sd: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	# Exactly one of en (active-high enable) or sd (shutdown, active-low enable) should
	# be specified, and it is mapped to a logic level en subsignal.
	if not (en is not None) ^ (sd is not None):
		raise ValueError('Only en or sd may be specified, not both!')

	io: list[SubsigArgT] = []

	io.append(Subsignal('rx', Pins(rx, dir = 'i', conn = conn, assert_width = 1)))
	io.append(Subsignal('tx', Pins(tx, dir = 'o', conn = conn, assert_width = 1)))

	if en is not None:
		io.append(Subsignal('en', Pins(en, dir = 'o', conn = conn, assert_width = 1)))

	if sd is not None:
		io.append(Subsignal('en', PinsN(sd, dir = 'o', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource('irda', number, *io)

def SPIResource(
	name_or_number: str | int, number: int | None = None, *,
	cs_n: str, clk: str, copi: str, cipo: str, int: str | None = None, reset: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
	role: Literal['controller', 'peripheral', 'generic'] = 'controller'
) -> Resource:

	if role not in ('controller', 'peripheral', 'generic'):
		raise ValueError(f'role must be one of \'controller\', \'peripheral\', or \'generic\' not {role!r}')

	# support unidirectional SPI
	if copi is None and cipo is None:
		raise ValueError('Either COPI or CIPO or both must be set, not none')

	io: list[SubsigArgT] = []

	if role == 'controller':
		io.append(Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn)))
		io.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
		if copi is not None:
			io.append(Subsignal('copi', Pins(copi, dir = 'o', conn = conn, assert_width = 1)))
		if cipo is not None:
			io.append(Subsignal('cipo', Pins(cipo, dir = 'i', conn = conn, assert_width = 1)))
	elif role == 'peripheral':
		io.append(Subsignal('cs', PinsN(cs_n, dir = 'i', conn = conn, assert_width = 1)))
		io.append(Subsignal('clk', Pins(clk, dir = 'i', conn = conn, assert_width = 1)))
		if copi is not None:
			io.append(Subsignal('copi', Pins(copi, dir = 'i', conn = conn, assert_width = 1)))
		if cipo is not None:
			io.append(Subsignal('cipo', Pins(cipo, dir = 'oe', conn = conn, assert_width = 1)))
	else: # generic
		io.append(Subsignal('cs', PinsN(cs_n, dir = 'io', conn = conn, assert_width = 1)))
		io.append(Subsignal('clk', Pins(clk, dir = 'io', conn = conn, assert_width = 1)))
		if copi is not None:
			io.append(Subsignal('copi', Pins(copi, dir = 'io', conn = conn, assert_width = 1)))
		if cipo is not None:
			io.append(Subsignal('cipo', Pins(cipo, dir = 'io', conn = conn, assert_width = 1)))

	if int is not None:
		if role == 'controller':
			io.append(Subsignal('int', Pins(int, dir = 'i', conn = conn)))
		elif role == 'peripheral':
			io.append(Subsignal('int', Pins(int, dir = 'oe', conn = conn, assert_width = 1)))
		else: # generic
			io.append(Subsignal('int', Pins(int, dir = 'io', conn = conn, assert_width = 1)))

	if reset is not None:
		if role == 'controller':
			io.append(Subsignal('reset', Pins(reset, dir = 'o', conn = conn)))
		elif role == 'peripheral':
			io.append(Subsignal('reset', Pins(reset, dir = 'i', conn = conn, assert_width = 1)))
		else:  # generic
			io.append(Subsignal('reset', Pins(reset, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'spi', ios = io)

def I2CResource(
	name_or_number: str | int, number: int | None = None, *,
	scl: str, sda: str, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	io: list[SubsigArgT] = []

	io.append(Subsignal('scl', Pins(scl, dir = 'io', conn = conn, assert_width = 1)))
	io.append(Subsignal('sda', Pins(sda, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'i2c', ios = io)

def DirectUSBResource(
	name_or_number: str | int, number: int | None = None, *,
	d_p: str, d_n: str, pullup: str | None = None, vbus_valid: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	io: list[SubsigArgT] = []

	io.append(Subsignal('d_p', Pins(d_p, dir = 'io', conn = conn, assert_width = 1)))
	io.append(Subsignal('d_n', Pins(d_n, dir = 'io', conn = conn, assert_width = 1)))

	if pullup:
		io.append(Subsignal('pullup', Pins(pullup, dir = 'o', conn = conn, assert_width = 1)))

	if vbus_valid:
		io.append(Subsignal('vbus_valid', Pins(vbus_valid, dir = 'i', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'usb', ios = io)

def ULPIResource(
	name_or_number: str | int, number: int | None = None, *,
	data: str, clk: str, dir: str, nxt: str, stp: str, rst: str | None = None,
	clk_dir: IODirection = 'i', rst_invert: bool = False, attrs: Attrs | None = None,
	clk_attrs: Attrs | None = None, conn: ResourceConn | None = None
) -> Resource:

	if clk_dir not in ('i', 'o'):
		raise ValueError(f'clk_dir should be \'i\' or \'o\' not {clk_dir!r}')

	clk_subsig = Subsignal('clk', Pins(clk, dir = clk_dir, conn = conn, assert_width = 1))
	# If the clock is an input, we must constrain it to be 60MHz.
	if clk_dir == 'i':
		clk_subsig.clock = Clock(60e6)
	if clk_attrs is not None:
		clk_subsig.attrs.update(clk_attrs)

	io: list[SubsigArgT] = []

	io.append(Subsignal('data', Pins(data, dir = 'io', conn = conn, assert_width = 8)))
	io.append(clk_subsig)
	io.append(Subsignal('dir', Pins(dir, dir = 'i', conn = conn, assert_width = 1)))
	io.append(Subsignal('nxt', Pins(nxt, dir = 'i', conn = conn, assert_width = 1)))
	io.append(Subsignal('stp', Pins(stp, dir = 'o', conn = conn, assert_width = 1)))

	if rst is not None:
		io.append(Subsignal(
			'rst', Pins(rst, dir = 'o', invert = rst_invert, conn = conn, assert_width = 1)
		))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'usb', ios = io)

def PS2Resource(
	name_or_number: str | int, number: int | None = None, *,
	clk: str, dat: str,
	conn:  ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	ios.append(Subsignal('clk', Pins(clk, dir = 'i', conn = conn, assert_width = 1)))
	ios.append(Subsignal('dat', Pins(dat, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'ps2', ios = ios)

def CANResource(
	name_or_number: str | int, number: int | None = None, *,
	rx: str, tx: str,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = [
		Subsignal('rx', Pins(rx, dir = 'i', conn = conn)),
		Subsignal('tx', Pins(tx, dir = 'o', conn = conn)),
	]

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'can', ios = ios)

def JTAGResource(
	name_or_number: str | int, number: int | None = None, *,
	tck: str, tms: str, tdi: str, tdo: str,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = [
		Subsignal('tck', Pins(tck, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tms', Pins(tms, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdi', Pins(tdi, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdo', Pins(tdo, dir = 'oe', conn = conn, assert_width = 1)),
	]
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(name_or_number, number, default_name = 'jtag', ios = ios)

def EthernetResource(
	name_or_number: str | int, number: int | None = None, *,
	rxck: str, rxd: str, txck: str, txd: str,
	rx_dv: str | None = None, rx_err: str | None = None, rx_ctl: str | None = None,
	tx_en: str | None = None, tx_err: str | None = None, tx_ctl: str | None = None,
	col: str | None = None, crs: str | None = None,
	mdc: str | None = None, mdio: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
	mdio_attrs: Attrs | None = None
) -> Resource:

	if len(rxd.split()) not in (4, 8):
		raise ValueError(
			f'{len(rxd.split())} names are specified ({rxd}) but one of (4, 8) was expected'
		)

	if len(txd.split()) not in (4, 8):
		raise ValueError(
			f'{len(txd.split())} names are specified ({txd}) but one of (4, 8) was expected'
		)

	ios: list[SubsigArgT] = [
		Subsignal('rx_clk', Pins(rxck, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('rx_dat', Pins(rxd, dir = 'i', conn = conn)),
		Subsignal('tx_clk', Pins(txck, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tx_dat', Pins(txd, dir = 'o', conn = conn)),
	]

	if rx_dv is not None and rx_err is not None:
		if rx_ctl is not None:
			raise ValueError('rx_ctl must be None!')
		ios.append(Subsignal('rx_dv', Pins(rx_dv, dir = 'i', conn = conn, assert_width = 1)))
		ios.append(Subsignal('rx_err', Pins(rx_err, dir = 'i', conn = conn, assert_width = 1)))
	elif rx_ctl is not None:
		ios.append(Subsignal('rx_ctl', Pins(rx_ctl, dir = 'i', conn = conn, assert_width = 1)))
	else:
		raise AssertionError('Must specify either MII RXDV + RXER pins or RGMII RXCTL')

	if tx_en is not None and tx_err is not None:
		if tx_ctl is not None:
			raise ValueError('tx_ctl must be None')
		ios.append(Subsignal('tx_en', Pins(tx_en, dir = 'o', conn = conn, assert_width = 1)))
		ios.append(Subsignal('tx_err', Pins(tx_err, dir = 'o', conn = conn, assert_width = 1)))
		if col is not None:
			ios.append(Subsignal('col', Pins(col, dir = 'i', conn = conn, assert_width = 1)))
		if crs is not None:
			ios.append(Subsignal('crs', Pins(crs, dir = 'i', conn = conn, assert_width = 1)))
	elif tx_ctl is not None:
		if col is not None and crs is not None:
			raise ValueError('col and crs must not be specified if tx_ctl is')
		ios.append(Subsignal('tx_ctl', Pins(tx_ctl, dir = 'o', conn = conn, assert_width = 1)))
	else:
		raise AssertionError('Must specify either MII TXDV + TXER pins or RGMII TXCTL')

	assert (rx_dv is not None and rx_err is not None) == (tx_en is not None and tx_err is not None)
	assert (rx_ctl is not None) == (tx_ctl is not None)

	if mdc is not None and mdio is not None and mdio_attrs is not None:
		ios.append(Subsignal('mdc', Pins(mdc, dir = 'o', conn = conn, assert_width = 1), mdio_attrs))
		ios.append(Subsignal('mdio', Pins(mdio, dir = 'io', conn = conn, assert_width = 1), mdio_attrs))
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(name_or_number, number, default_name = 'eth', ios = ios)

def HyperBusResource(
	name_or_number: str | int, number: int | None = None, *,
	bus_type: Literal['controller', 'peripheral'],
	cs_n: str, clk_p: str, clk_n: str | None, dq: str, rwds: str, rst_n: str | None = None,
	rsto_n: str | None = None, int_n: str | None = None,
	conn: ResourceConn | None = None, diff_attrs = None, attrs: Attrs | None = None,
):
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

def PCIeBusResources(
	name_or_number: str | int, number: int | None = None, *,
	perst_n: str, refclk_p: str, refclk_n: str,
	pet0_p: str, pet0_n: str, per0_p: str, per0_n: str,
	pet1_p: str | None = None, pet1_n: str | None = None, per1_p: str | None = None, per1_n: str | None = None,
	pet2_p: str | None = None, pet2_n: str | None = None, per2_p: str | None = None, per2_n: str | None = None,
	pet3_p: str | None = None, pet3_n: str | None = None, per3_p: str | None = None, per3_n: str | None = None,
	pet4_p: str | None = None, pet4_n: str | None = None, per4_p: str | None = None, per4_n: str | None = None,
	pet5_p: str | None = None, pet5_n: str | None = None, per5_p: str | None = None, per5_n: str | None = None,
	pet6_p: str | None = None, pet6_n: str | None = None, per6_p: str | None = None, per6_n: str | None = None,
	pet7_p: str | None = None, pet7_n: str | None = None, per7_p: str | None = None, per7_n: str | None = None,
	pet8_p: str | None = None, pet8_n: str | None = None, per8_p: str | None = None, per8_n: str | None = None,
	pet9_p: str | None = None, pet9_n: str | None = None, per9_p: str | None = None, per9_n: str | None = None,
	pet10_p: str | None = None, pet10_n: str | None = None, per10_p: str | None = None, per10_n: str | None = None,
	pet11_p: str | None = None, pet11_n: str | None = None, per11_p: str | None = None, per11_n: str | None = None,
	pet12_p: str | None = None, pet12_n: str | None = None, per12_p: str | None = None, per12_n: str | None = None,
	pet13_p: str | None = None, pet13_n: str | None = None, per13_p: str | None = None, per13_n: str | None = None,
	pet14_p: str | None = None, pet14_n: str | None = None, per14_p: str | None = None, per14_n: str | None = None,
	pet15_p: str | None = None, pet15_n: str | None = None, per15_p: str | None = None, per15_n: str | None = None,
	pet16_p: str | None = None, pet16_n: str | None = None, per16_p: str | None = None, per16_n: str | None = None,
	pet17_p: str | None = None, pet17_n: str | None = None, per17_p: str | None = None, per17_n: str | None = None,
	pet18_p: str | None = None, pet18_n: str | None = None, per18_p: str | None = None, per18_n: str | None = None,
	pet19_p: str | None = None, pet19_n: str | None = None, per19_p: str | None = None, per19_n: str | None = None,
	pet20_p: str | None = None, pet20_n: str | None = None, per20_p: str | None = None, per20_n: str | None = None,
	pet21_p: str | None = None, pet21_n: str | None = None, per21_p: str | None = None, per21_n: str | None = None,
	pet22_p: str | None = None, pet22_n: str | None = None, per22_p: str | None = None, per22_n: str | None = None,
	pet23_p: str | None = None, pet23_n: str | None = None, per23_p: str | None = None, per23_n: str | None = None,
	pet24_p: str | None = None, pet24_n: str | None = None, per24_p: str | None = None, per24_n: str | None = None,
	pet25_p: str | None = None, pet25_n: str | None = None, per25_p: str | None = None, per25_n: str | None = None,
	pet26_p: str | None = None, pet26_n: str | None = None, per26_p: str | None = None, per26_n: str | None = None,
	pet27_p: str | None = None, pet27_n: str | None = None, per27_p: str | None = None, per27_n: str | None = None,
	pet28_p: str | None = None, pet28_n: str | None = None, per28_p: str | None = None, per28_n: str | None = None,
	pet29_p: str | None = None, pet29_n: str | None = None, per29_p: str | None = None, per29_n: str | None = None,
	pet30_p: str | None = None, pet30_n: str | None = None, per30_p: str | None = None, per30_n: str | None = None,
	pet31_p: str | None = None, pet31_n: str | None = None, per31_p: str | None = None, per31_n: str | None = None,
	wake_n: str | None = None, smdat: str | None = None, smclk: str | None = None, clkreq_n: str | None = None,
	pwrbrk_n: str | None = None, tck: str | None = None, tdi: str | None = None, tdo: str | None = None,
	tms: str | None = None, trst_n: str | None = None, invert: bool = False, conn: ResourceConn | None = None,
	attrs: Attrs = Attrs(), refclk_attrs: Attrs = Attrs(), lane_attrs: Attrs = Attrs()
) -> list[Resource]:
	'''
	Create a PCIe bus resource.

	This will create a collection of PCIe bus resources, from the smallest up to the largest possible
	size with the provided signals.

	Each resource is suffixed with the width of the bus, all possible width are as follows:

	* x1
	* x2
	* x4
	* x6
	* x8
	* x12
	* x16
	* x24
	* x32

	For instance, if you provide the signals for a x16 PCIe bus, you will also get every size down to
	x1.

	.. code-block:: Python

		pcie = PCIeBusResouces('pcie', 0, ...) # Signals up to x16
		pcie[0] # pcie_x1
		pcie[1] # pcie_x2
		pcie[2] # pcie_x4
		pcie[3] # pcie_x6
		pcie[4] # pcie_x8
		pcie[5] # pcie_x12
		pcie[6] # pcie_x16
	'''

	resources: list[Resource]  = []
	io_common: list[Subsignal] = []

	io_common.append(Subsignal(
		'perst', PinsN(perst_n, dir = 'i', conn = conn, assert_width = 1), attrs
	))
	io_common.append(Subsignal(
		'refclk', DiffPairs(refclk_p, refclk_n, dir = 'i', conn = conn, assert_width = 1), refclk_attrs
	))

	jtag_sigs = (tck, tdi, tdo, tms, trst_n,) # type: ignore

	if wake_n is not None:
		io_common.append(Subsignal(
			'wake', PinsN(wake_n, dir = 'i', conn = conn, assert_width = 1), attrs
		))

	if smdat is not None and smclk is not None:
		io_common.append(Subsignal(
			'smdat', Pins(smdat, dir = 'io', conn = conn, assert_width = 1), attrs
		))
		io_common.append(Subsignal(
			'smclk', Pins(smclk, dir = 'io', conn = conn, assert_width = 1), attrs
		))

	if all(jtag_sigs):
		# HACK(aki): Type coercion, `all` above ensure we have no Nones
		if TYPE_CHECKING:
			jtag_sigs: tuple[str, ...] = jtag_sigs

		io_common.append(Subsignal(
			'tck', Pins(jtag_sigs[0], dir = 'i', conn = conn, assert_width = 1), attrs
		))
		io_common.append(Subsignal(
			'tdi', Pins(jtag_sigs[1], dir = 'i', conn = conn, assert_width = 1), attrs
		))
		io_common.append(Subsignal(
			'tdo', Pins(jtag_sigs[2], dir = 'o', conn = conn, assert_width = 1), attrs
		))
		io_common.append(Subsignal(
			'tms', Pins(jtag_sigs[3], dir = 'i', conn = conn, assert_width = 1), attrs
		))
		io_common.append(Subsignal(
			'trst', PinsN(jtag_sigs[4], dir = 'i', conn = conn, assert_width = 1), attrs
		))

	if clkreq_n is not None:
		io_common.append(Subsignal(
			'clkreq', PinsN(clkreq_n, dir = 'o', conn = conn, assert_width = 1), attrs
		))

	io_x1 = list(io_common)
	io_x1.append(Subsignal(
		'pet0', DiffPairs(pet0_p, pet0_n, dir = 'o', conn = conn, assert_width = 1), lane_attrs
	))
	io_x1.append(Subsignal(
		'per0', DiffPairs(per0_p, per0_n, dir = 'i', conn = conn, assert_width = 1), lane_attrs
	))

	resources.append(Resource.family(
		name_or_number, number, default_name = 'pcie', ios = io_x1, name_suffix = 'x1'
	))

	io_x2: list[Subsignal] | None = None
	io_x4: list[Subsignal] | None = None
	io_x6: list[Subsignal] | None = None # XXX(aki): Non-standard
	io_x8: list[Subsignal] | None = None
	io_x12: list[Subsignal] | None = None # XXX(aki): PCIe <= 4.0
	io_x16: list[Subsignal] | None = None
	io_x24: list[Subsignal] | None = None # XXX(aki): Non-standard
	io_x32: list[Subsignal] | None = None # XXX(aki): PCIe <= 4.0

	x2_sigs = (
		pet1_p, pet1_n, per1_p, per1_n,
	) # type: ignore
	x4_sigs = (
		pet2_p, pet2_n, per2_p, per2_n, pet3_p, pet3_n, per3_p, per3_n,
	) # type: ignore
	x6_sigs = (
		pet4_p, pet4_n, per4_p, per4_n, pet5_p, pet5_n, per5_p, per5_n,
	) # type: ignore
	x8_sigs = (
		pet6_p, pet6_n, per6_p, per6_n, pet7_p, pet7_n, per7_p, per7_n,
	) # type: ignore
	x12_sigs = (
		pet8_p, pet8_n, per8_p, per8_n, pet9_p, pet9_n, per9_p, per9_n,
		pet10_p, pet10_n, per10_p, per10_n, pet11_p, pet11_n, per11_p, per11_n,
	) # type: ignore
	x16_sigs = (
		pet12_p, pet12_n, per12_p, per12_n, pet13_p, pet13_n, per13_p, per13_n,
		pet14_p, pet14_n, per14_p, per14_n, pet15_p, pet15_n, per15_p, per15_n,
	) # type: ignore
	x24_sigs = (
		pet16_p, pet16_n, per16_p, per16_n, pet17_p, pet17_n, per17_p, per17_n,
		pet18_p, pet18_n, per18_p, per18_n, pet19_p, pet19_n, per19_p, per19_n,
		pet20_p, pet20_n, per20_p, per20_n, pet21_p, pet21_n, per21_p, per21_n,
		pet22_p, pet22_n, per22_p, per22_n, pet23_p, pet23_n, per23_p, per23_n,
	) # type: ignore
	x32_sigs = (
		pet24_p, pet24_n, per24_p, per24_n, pet25_p, pet25_n, per25_p, per25_n,
		pet26_p, pet26_n, per26_p, per26_n, pet27_p, pet27_n, per27_p, per27_n,
		pet28_p, pet28_n, per28_p, per28_n, pet29_p, pet29_n, per29_p, per29_n,
		pet30_p, pet30_n, per30_p, per30_n, pet31_p, pet31_n, per31_p, per31_n,
	) # type: ignore

	# If we can also build an x2, do so
	if all(x2_sigs):
		io_x2 = list(io_x1)

		# HACK(aki): Type coercion, `all` above ensure we have no Nones
		if TYPE_CHECKING:
			x2_sigs: tuple[str, ...] = x2_sigs

		io_x2.append(Subsignal(
			'pet1', DiffPairs(x2_sigs[0], x2_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
		))
		io_x2.append(Subsignal(
			'per1', DiffPairs(x2_sigs[2], x2_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
		))

		resources.append(Resource.family(
			name_or_number, number, default_name = 'pcie', ios = io_x2, name_suffix = 'x2'
		))
	elif any(x2_sigs):
		warn(
			'Only a subset of the PCIe x2 signals were provided, was this intentional? '
			'This is an uncommon bus width, did you intend for a PCIe x4?',
			ResourceWarning, stacklevel = 2
		)

	# If we could build a x2, and we have the signals for an x4, also make one
	if io_x2 is not None:
		if all(x4_sigs):
			io_x4 = list(io_x2)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x4_sigs: tuple[str, ...] = x4_sigs

			io_x4.append(Subsignal(
				'pet2', DiffPairs(x4_sigs[0], x4_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x4.append(Subsignal(
				'per2', DiffPairs(x4_sigs[2], x4_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x4.append(Subsignal(
				'pet3', DiffPairs(x4_sigs[4], x4_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x4.append(Subsignal(
				'per3', DiffPairs(x4_sigs[6], x4_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			if pwrbrk_n is not None:
				io_x4.append(Subsignal('pwrbrk', PinsN(pwrbrk_n, dir = 'o', conn = conn, assert_width = 1)))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x4, name_suffix = 'x4'
			))
		elif any(x4_sigs):
			warn(
				'Only a subset of the PCIe x4 signals were provided, was this intentional?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x4, and we have the signals for an x6, also make one
	if io_x4 is not None:
		if all(x6_sigs):
			io_x6 = list(io_x4)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x6_sigs: tuple[str, ...] = x6_sigs

			io_x6.append(Subsignal(
				'pet4', DiffPairs(x6_sigs[0], x6_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x6.append(Subsignal(
				'per4', DiffPairs(x6_sigs[2], x6_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x6.append(Subsignal(
				'pet5', DiffPairs(x6_sigs[4], x6_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x6.append(Subsignal(
				'per5', DiffPairs(x6_sigs[6], x6_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x6, name_suffix = 'x6'
			))
		elif any(x6_sigs):
			warn(
				'Only a subset of the PCIe x6 signals were provided, was this intentional? '
				'This is an uncommon bus width, did you intend for a PCIe x8?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x6, and we have the signals for an x8, also make one
	if io_x6 is not None:
		if all(x8_sigs):
			io_x8 = list(io_x6)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x8_sigs: tuple[str, ...] = x8_sigs

			io_x8.append(Subsignal(
				'pet6', DiffPairs(x8_sigs[0], x8_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x8.append(Subsignal(
				'per6', DiffPairs(x8_sigs[2], x8_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x8.append(Subsignal(
				'pet7', DiffPairs(x8_sigs[4], x8_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x8.append(Subsignal(
				'per7', DiffPairs(x8_sigs[6], x8_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x8, name_suffix = 'x8'
			))
		elif any(x8_sigs):
			warn(
				'Only a subset of the PCIe x8 signals were provided, was this intentional?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x8, and we have the signals for an x12, also make one
	if io_x8 is not None:
		if all(x12_sigs):
			io_x12 = list(io_x8)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x12_sigs: tuple[str, ...] = x12_sigs

			io_x12.append(Subsignal(
				'pet8', DiffPairs(x12_sigs[0], x12_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'per8', DiffPairs(x12_sigs[2], x12_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'pet9', DiffPairs(x12_sigs[4], x12_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'per9', DiffPairs(x12_sigs[6], x12_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'pet10', DiffPairs(x12_sigs[8], x12_sigs[9], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'per10', DiffPairs(x12_sigs[10], x12_sigs[11], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'pet11', DiffPairs(x12_sigs[12], x12_sigs[13], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x12.append(Subsignal(
				'per11', DiffPairs(x12_sigs[14], x12_sigs[15], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x12, name_suffix = 'x12'
			))
		elif any(x12_sigs):
			warn(
				'Only a subset of the PCIe x12 signals were provided, was this intentional? '
				'This is an uncommon bus width, did you intend for a PCIe x16?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x12, and we have the signals for an x16, also make one
	if io_x12 is not None:
		if all(x16_sigs):
			io_x16 = list(io_x12)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x16_sigs: tuple[str, ...] = x16_sigs

			io_x16.append(Subsignal(
				'pet12', DiffPairs(x16_sigs[0], x16_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'per12', DiffPairs(x16_sigs[2], x16_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'pet13', DiffPairs(x16_sigs[4], x16_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'per13', DiffPairs(x16_sigs[6], x16_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'pet14', DiffPairs(x16_sigs[8], x16_sigs[9], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'per14', DiffPairs(x16_sigs[10], x16_sigs[11], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'pet15', DiffPairs(x16_sigs[12], x16_sigs[13], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x16.append(Subsignal(
				'per15', DiffPairs(x16_sigs[14], x16_sigs[15], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x16, name_suffix = 'x16'
			))
		elif any(x16_sigs):
			warn(
				'Only a subset of the PCIe x16 signals were provided, was this intentional?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x16, and we have the signals for an x24, also make one
	if io_x16 is not None:
		if all(x24_sigs):
			io_x24 = list(io_x16)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x24_sigs: tuple[str, ...] = x24_sigs

			io_x24.append(Subsignal(
				'pet16', DiffPairs(x24_sigs[0], x24_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per16', DiffPairs(x24_sigs[2], x24_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet17', DiffPairs(x24_sigs[4], x24_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per17', DiffPairs(x24_sigs[6], x24_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet18', DiffPairs(x24_sigs[8], x24_sigs[9], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per18', DiffPairs(x24_sigs[10], x24_sigs[11], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet19', DiffPairs(x24_sigs[12], x24_sigs[13], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per19', DiffPairs(x24_sigs[14], x24_sigs[15], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet20', DiffPairs(x24_sigs[16], x24_sigs[17], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per20', DiffPairs(x24_sigs[18], x24_sigs[19], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet21', DiffPairs(x24_sigs[20], x24_sigs[21], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per21', DiffPairs(x24_sigs[22], x24_sigs[23], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet22', DiffPairs(x24_sigs[24], x24_sigs[25], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per22', DiffPairs(x24_sigs[26], x24_sigs[27], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'pet23', DiffPairs(x24_sigs[28], x24_sigs[29], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x24.append(Subsignal(
				'per23', DiffPairs(x24_sigs[30], x24_sigs[31], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x24, name_suffix = 'x24'
			))
		elif any(x24_sigs):
			warn(
				'Only a subset of the PCIe x24 signals were provided, was this intentional?',
				ResourceWarning, stacklevel = 2
			)

	# If we could build a x24, and we have the signals for an x32, also make one
	if io_x24 is not None:
		if all(x32_sigs):
			io_x32 = list(io_x24)

			# HACK(aki): Type coercion, `all` above ensure we have no Nones
			if TYPE_CHECKING:
				x32_sigs: tuple[str, ...] = x32_sigs

			io_x32.append(Subsignal(
				'pet24', DiffPairs(x32_sigs[0], x32_sigs[1], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per24', DiffPairs(x32_sigs[2], x32_sigs[3], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet25', DiffPairs(x32_sigs[4], x32_sigs[5], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per25', DiffPairs(x32_sigs[6], x32_sigs[7], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet26', DiffPairs(x32_sigs[8], x32_sigs[9], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per26', DiffPairs(x32_sigs[10], x32_sigs[11], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet27', DiffPairs(x32_sigs[12], x32_sigs[13], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per27', DiffPairs(x32_sigs[14], x32_sigs[15], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet28', DiffPairs(x32_sigs[16], x32_sigs[17], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per28', DiffPairs(x32_sigs[18], x32_sigs[19], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet29', DiffPairs(x32_sigs[20], x32_sigs[21], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per29', DiffPairs(x32_sigs[22], x32_sigs[23], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet30', DiffPairs(x32_sigs[24], x32_sigs[25], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per30', DiffPairs(x32_sigs[26], x32_sigs[27], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'pet31', DiffPairs(x32_sigs[28], x32_sigs[29], dir = 'o', conn = conn, assert_width = 1), lane_attrs
			))
			io_x32.append(Subsignal(
				'per31', DiffPairs(x32_sigs[30], x32_sigs[31], dir = 'i', conn = conn, assert_width = 1), lane_attrs
			))

			resources.append(Resource.family(
				name_or_number, number, default_name = 'pcie', ios = io_x32, name_suffix = 'x32'
			))
		elif any(x32_sigs):
			warn(
				'Only a subset of the PCIe x32 signals were provided, was this intentional?',
				ResourceWarning, stacklevel = 2
			)

	if not any((io_x4, io_x6, io_x8, io_x12, io_x16, io_x24, io_x32)) and pwrbrk_n is not None:
		warn(
			'You specified a pwrbrk_n signal, however not enough PCIe lines for at least an x4 bus. '
			'Therefore pwrbrk was not used. Was this intentional?',
			ResourceWarning, stacklevel = 2
		)

	return resources
