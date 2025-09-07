# SPDX-License-Identifier: BSD-2-Clause

from typing        import Literal

from ....build.dsl import Attrs, Pins, PinsN, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'I2CResource',
	'IrDAResource',
	'JTAGResource',
	'PS2Resource',
	'SPIResource',
	'UARTResource',
)

def I2CResource(
	name_or_number: str | int, number: int | None = None, *,
	scl: str, sda: str, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

	io: list[SubsigArgT] = []

	io.append(Subsignal('scl', Pins(scl, dir = 'io', conn = conn, assert_width = 1)))
	io.append(Subsignal('sda', Pins(sda, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'i2c', ios = io)

def IrDAResource(
	number: int, *,
	rx: str, tx: str, en: str | None = None, sd: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

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

def JTAGResource(
	name_or_number: str | int, number: int | None = None, *,
	tck: str, tms: str, tdi: str, tdo: str,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

	ios: list[SubsigArgT] = [
		Subsignal('tck', Pins(tck, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tms', Pins(tms, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdi', Pins(tdi, dir = 'i', conn = conn, assert_width = 1)),
		Subsignal('tdo', Pins(tdo, dir = 'oe', conn = conn, assert_width = 1)),
	]
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(name_or_number, number, default_name = 'jtag', ios = ios)

def PS2Resource(
	name_or_number: str | int, number: int | None = None, *,
	clk: str, dat: str,
	conn:  ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

	ios: list[SubsigArgT] = []

	ios.append(Subsignal('clk', Pins(clk, dir = 'i', conn = conn, assert_width = 1)))
	ios.append(Subsignal('dat', Pins(dat, dir = 'io', conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'ps2', ios = ios)

def SPIResource(
	name_or_number: str | int, number: int | None = None, *,
	cs_n: str, clk: str, copi: str, cipo: str, int: str | None = None, reset: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
	role: Literal['controller', 'peripheral', 'generic'] = 'controller'
) -> Resource:
	'''
	.. todo:: Document Me
	'''

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

def UARTResource(
	name_or_number: str | int, number: int | None = None, *,
	rx: str, tx: str, rts: str | None = None, cts: str | None = None,
	dtr: str | None = None, dsr: str | None = None, dcd: str | None = None,
	ri: str | None = None, conn: ResourceConn | None = None,
	attrs: Attrs | None = None, role: str | None  = None
) -> Resource:
	'''
	.. todo:: Document Me
	'''

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
