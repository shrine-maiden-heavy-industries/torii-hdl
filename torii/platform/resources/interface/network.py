# SPDX-License-Identifier: BSD-2-Clause

from ....build.dsl import Attrs, Pins, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'CANResource',
	'EthernetResource',
)

def CANResource(
	name_or_number: str | int, number: int | None = None, *,
	rx: str, tx: str,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

	ios: list[SubsigArgT] = [
		Subsignal('rx', Pins(rx, dir = 'i', conn = conn)),
		Subsignal('tx', Pins(tx, dir = 'o', conn = conn)),
	]

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'can', ios = ios)

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
	'''
	.. todo:: Document Me
	'''

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
