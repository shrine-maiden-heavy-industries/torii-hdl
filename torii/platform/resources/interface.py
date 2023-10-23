# SPDX-License-Identifier: BSD-2-Clause

from typing   import Literal, Optional, Union

from ...build import Attrs, Clock, Pins, PinsN, Resource, Subsignal, DiffPairs

__all__ = (
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
)

def UARTResource(
	*args,
	rx: str, tx: str, rts: Optional[str] = None, cts: Optional[str] = None,
	dtr: Optional[str] = None, dsr: Optional[str] = None, dcd: Optional[str] = None,
	ri: Optional[str] = None, conn: Optional[Union[tuple[str, int], str]] = None,
	attrs: Optional[Attrs] = None, role: Optional[str]  = None
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

	io = []

	io.append(Subsignal('rx', Pins(rx, dir = 'i', conn = conn, assert_width = 1)))
	io.append(Subsignal('tx', Pins(tx, dir = 'o', conn = conn, assert_width = 1)))

	if rts is not None:
		io.append(Subsignal('rts', Pins(rts, dir = dte_to_dce, conn = conn, assert_width = 1)))

	if cts is not None:
		io.append(Subsignal('cts', Pins(cts, dir = dce_to_dte, conn = conn, assert_width = 1)))

	if dtr is not None:
		io.append(Subsignal('dtr', Pins(dtr, dir = dte_to_dce, conn = conn, assert_width = 1)))

	if dsr is not None:
		io.append(Subsignal('dsr', Pins(dsr, dir = dce_to_dte, conn = conn, assert_width = 1)))

	if dcd is not None:
		io.append(Subsignal('dcd', Pins(dcd, dir = dce_to_dte, conn = conn, assert_width = 1)))

	if ri is not None:
		io.append(Subsignal('ri', Pins(ri, dir = dce_to_dte, conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(*args, default_name = 'uart', ios = io)


def IrDAResource(
	number: int, *, rx: str, tx: str, en: Optional[str] = None, sd: Optional[str] = None,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:
	# Exactly one of en (active-high enable) or sd (shutdown, active-low enable) should
	# be specified, and it is mapped to a logic level en subsignal.
	if not (en is not None) ^ (sd is not None):
		raise ValueError('Only en or sd may be specified, not both!')

	io = []

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
	*args,
	cs_n: str, clk: str, copi: str, cipo: str, int: str = None, reset: str = None,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None,
	role: Literal['controller', 'peripheral'] = 'controller'
) -> Resource:

	if role not in ('controller', 'peripheral'):
		raise ValueError(f'role is expected to be \'controller\' or \'peripheral\', not {role!r}')

	# support unidirectional SPI
	if copi is None and cipo is None:
		raise ValueError('Either COPI or CIPO or both must be set, not none')

	io = []

	if role == 'controller':
		io.append(Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn)))
		io.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
		if copi is not None:
			io.append(Subsignal('copi', Pins(copi, dir = 'o', conn = conn, assert_width = 1)))
		if cipo is not None:
			io.append(Subsignal('cipo', Pins(cipo, dir = 'i', conn = conn, assert_width = 1)))
	else:  # peripheral
		io.append(Subsignal('cs', PinsN(cs_n, dir = 'i', conn = conn, assert_width = 1)))
		io.append(Subsignal('clk', Pins(clk, dir = 'i', conn = conn, assert_width = 1)))
		if copi is not None:
			io.append(Subsignal('copi', Pins(copi, dir = 'i', conn = conn, assert_width = 1)))
		if cipo is not None:
			io.append(Subsignal('cipo', Pins(cipo, dir = 'oe', conn = conn, assert_width = 1)))

	if int is not None:
		if role == 'controller':
			io.append(Subsignal('int', Pins(int, dir = 'i', conn = conn)))
		else:
			io.append(Subsignal('int', Pins(int, dir = 'oe', conn = conn, assert_width = 1)))

	if reset is not None:
		if role == 'controller':
			io.append(Subsignal('reset', Pins(reset, dir = 'o', conn = conn)))
		else:
			io.append(Subsignal('reset', Pins(reset, dir = 'i', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(*args, default_name = 'spi', ios = io)


def I2CResource(
	*args,
	scl: str, sda: str, conn: Optional[Union[tuple[str, int], int]] = None,
	attrs: Optional[Attrs] = None
) -> Resource:

	io = []

	io.append(Subsignal('scl', Pins(scl, dir = 'io', conn = conn, assert_width = 1)))
	io.append(Subsignal('sda', Pins(sda, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(*args, default_name = 'i2c', ios = io)


def DirectUSBResource(
	*args,
	d_p: str, d_n: str, pullup: Optional[str] = None, vbus_valid: Optional[str] = None,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:

	io = []

	io.append(Subsignal('d_p', Pins(d_p, dir = 'io', conn = conn, assert_width = 1)))
	io.append(Subsignal('d_n', Pins(d_n, dir = 'io', conn = conn, assert_width = 1)))

	if pullup:
		io.append(Subsignal('pullup', Pins(pullup, dir = 'o', conn = conn, assert_width = 1)))

	if vbus_valid:
		io.append(Subsignal('vbus_valid', Pins(vbus_valid, dir = 'i', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(*args, default_name = 'usb', ios = io)


def ULPIResource(
	*args,
	data: str, clk: str, dir: str, nxt: str, stp: str, rst: Optional[str] = None,
	clk_dir: Literal['i', 'o'] = 'i', rst_invert: bool = False, attrs: Optional[Attrs] = None,
	clk_attrs: Optional[Attrs] = None, conn: Optional[Union[tuple[str, int], int]] = None
) -> Resource:

	if clk_dir not in ('i', 'o'):
		raise ValueError(f'clk_dir should be \'i\' or \'o\' not {clk_dir!r}')

	clk_subsig = Subsignal('clk', Pins(clk, dir = clk_dir, conn = conn, assert_width = 1))
	# If the clock is an input, we must constrain it to be 60MHz.
	if clk_dir == 'i':
		clk_subsig.clock = Clock(60e6)
	if clk_attrs is not None:
		clk_subsig.attrs.update(clk_attrs)

	io = []

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

	return Resource.family(*args, default_name = 'usb', ios = io)


def PS2Resource(
	*args,
	clk: str, dat: str,
	conn :  Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:
	ios = []

	ios.append(Subsignal('clk', Pins(clk, dir = 'i', conn = conn, assert_width = 1))),
	ios.append(Subsignal('dat', Pins(dat, dir = 'io', conn = conn, assert_width = 1))),

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(*args, default_name = 'ps2', ios = ios)

def CANResource(
	*args, rx: str, tx: str,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:
	ios = [
		Subsignal('rx', Pins(rx, dir = 'i', conn = conn)),
		Subsignal('tx', Pins(tx, dir = 'o', conn = conn)),
	]

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(*args, default_name = 'can', ios = ios)

def JTAGResource(
	*args, tck: str, tms: str, tdi: str, tdo: str,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:
	ios = [
		Subsignal('tck', Pins(tck, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tms', Pins(tms, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdi', Pins(tdi, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdo', Pins(tdo, dir = 'oe', conn = conn, assert_width = 1)),
	]
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(*args, default_name = 'jtag', ios = ios)

def EthernetResource(
	*args,
	rxck: str, rxd: str, txck: str, txd: str,
	rx_dv: Optional[str] = None, rx_err: Optional[str] = None, rx_ctl: Optional[str] = None,
	tx_en: Optional[str] = None, tx_err: Optional[str] = None, tx_ctl: Optional[str] = None,
	col: Optional[str] = None, crs: Optional[str] = None,
	mdc: Optional[str] = None, mdio: Optional[str] = None,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None,
	mdio_attrs: Optional[Attrs] = None
) -> Resource:

	if len(rxd.split()) not in (4, 8):
		raise ValueError(
			f'{len(rxd.split())} names are specified ({rxd}) but one of (4, 8) was expected'
		)

	if len(txd.split()) not in (4, 8):
		raise ValueError(
			f'{len(txd.split())} names are specified ({txd}) but one of (4, 8) was expected'
		)


	ios = [
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

	if mdc is not None and mdio is not None:
		ios.append(Subsignal('mdc', Pins(mdc, dir = 'o', conn = conn, assert_width = 1), mdio_attrs))
		ios.append(Subsignal('mdio', Pins(mdio, dir = 'io', conn = conn, assert_width = 1), mdio_attrs))
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(*args, default_name = 'eth', ios = ios)

def HyperBusResource(
	*args, bus_type: Literal['controller', 'peripheral'],
	cs_n: str, clk_p: str, clk_n: Optional[str], dq: str, rwds: str, rst_n: Optional[str] = None,
	rsto_n: Optional[str] = None, int_n: Optional[str] = None,
	conn: Optional[Union[tuple[str, int], int]] = None, diff_attrs = None, attrs: Optional[Attrs] = None,
):
	ios = []


	ios.append(
		Subsignal('cs', PinsN(
			cs_n, dir = 'o' if bus_type == 'controller' else 'i', conn = conn, assert_width = 1
		)),
		Subsignal('dq',   Pins(dq, dir = 'io', conn = conn, assert_width = 8)),
		Subsignal('rwds', Pins(rwds, dir = 'io', conn = conn, assert_width = 1)),
	)

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
				rst_n, dir = 'i' if bus_type == 'controller' else 'o', conn = conn, assert_width = 1
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

	return Resource.family(*args, default_name = 'hyperbus', ios = ios)
