# SPDX-License-Identifier: BSD-2-Clause

from enum          import Enum, auto, unique

from ....build.dsl import Attrs, Pins, PinsN, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'NORFlashResources',
	'QSPIDataMode',
	'QSPIFlashResource',
	'QSPIMode',
	'SDCardResources',
	'SPIFlashResources',
)

@unique
class QSPIMode(Enum):
	'''
	.. todo:: Document Me
	'''

	Single       = auto()
	DualStacked  = auto()
	DualParallel = auto()

@unique
class QSPIDataMode(Enum):
	'''
	.. todo:: Document Me
	'''

	x1 = auto()
	x2 = auto()
	x4 = auto()
	x8 = auto()

def NORFlashResources(
	name_or_number: str | int, number: int | None = None, *,
	rst: str | None = None, byte_n: str | None = None,
	cs_n: str, oe_n: str, we_n: str, wp_n: str, by: str, a: str, dq: str,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> list[Resource]:
	'''
	.. todo:: Document Me
	'''

	resources: list[Resource]   = []
	io_common: list[SubsigArgT] = []

	if rst is not None:
		io_common.append(Subsignal('rst', Pins(rst, dir = 'o', conn = conn, assert_width = 1)))

	io_common.append(Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn, assert_width = 1)))
	io_common.append(Subsignal('oe', PinsN(oe_n, dir = 'o', conn = conn, assert_width = 1)))
	io_common.append(Subsignal('we', PinsN(we_n, dir = 'o', conn = conn, assert_width = 1)))
	io_common.append(Subsignal('wp', PinsN(wp_n, dir = 'o', conn = conn, assert_width = 1)))
	io_common.append(Subsignal('rdy', Pins(by, dir = 'i', conn = conn, assert_width = 1)))

	if byte_n is None:
		io_8bit = list(io_common)
		io_8bit.append(Subsignal('a', Pins(a, dir = 'o', conn = conn)))
		io_8bit.append(Subsignal('dq', Pins(dq, dir = 'io', conn = conn, assert_width = 8)))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'nor_flash', ios = io_8bit, name_suffix = '8bit'
		))
	else:
		*dq_0_14, dq15_am1 = dq.split()

		# If present in a requested resource, this pin needs to be strapped correctly.
		io_common.append(Subsignal('byte', PinsN(byte_n, dir = 'o', conn = conn, assert_width = 1)))

		io_8bit = list(io_common)
		io_8bit.append(Subsignal('a', Pins(' '.join((dq15_am1, a)), dir = 'o', conn = conn)))
		io_8bit.append(Subsignal('dq', Pins(' '.join(dq_0_14[:8]), dir = 'io', conn = conn, assert_width = 8)))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'nor_flash', ios = io_8bit, name_suffix = '8bit'
		))

		io_16bit = list(io_common)
		io_16bit.append(Subsignal('a', Pins(a, dir = 'o', conn = conn)))
		io_16bit.append(Subsignal('dq', Pins(dq, dir = 'io', conn = conn, assert_width = 16)))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'nor_flash', ios = io_16bit, name_suffix = '16bit'
		))

	return resources

# TODO(aki): Merge into `SPIFlashResource`
def QSPIFlashResource(
	name_or_number: str | int, number: int | None = None, *,
	cs_n: str, clk: str, mode: QSPIMode, data_mode: QSPIDataMode,
	dq: str | None = None, dq_a: str | None = None, dq_b: str | None = None,
	clk_fb: str | None = None, conn: ResourceConn | None = None, attrs: Attrs | None = None
):
	'''
	.. todo:: Document Me
	'''

	if not isinstance(mode, QSPIMode) or not isinstance(data_mode, QSPIDataMode):
		raise AssertionError('mode must be a QSPIMode and data_mode a QSPIDataMode')
	elif mode == QSPIMode.Single and data_mode == QSPIDataMode.x8:
		raise AssertionError('Cannot use x8 data mode in QSPI single mode')
	elif mode == QSPIMode.DualStacked and data_mode == QSPIDataMode.x8:
		raise AssertionError('Cannot use x8 data mode in QSPI dual stacked mode')
	elif mode == QSPIMode.DualParallel and data_mode != QSPIDataMode.x8:
		raise AssertionError('Must use x8 data mode in QSPI dual parallel mode')

	clk_count = 2 if mode == QSPIMode.DualParallel else 1
	cs_count = 1 if mode == QSPIMode.Single else 2

	ios: list[SubsigArgT] = [
		Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn, assert_width = cs_count)),
		Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = clk_count)),
	]

	if mode == QSPIMode.DualParallel:
		if dq is not None and (dq_a is None or dq_b is None):
			raise ValueError(f'\'dq\' must be None and \'dq_a\' and \'dq_b\' must be specified for mode \'{mode}\'')
		ios.append(Subsignal('dq_a', Pins(dq_a, dir = 'io', conn = conn, assert_width = 4)))
		ios.append(Subsignal('dq_b', Pins(dq_b, dir = 'io', conn = conn, assert_width = 4)))
	else:
		if dq is None and (dq_a is not None or dq_b is not None):
			raise ValueError(f'\'dq\' must be specified and \'dq_a\' and \'dq_b\' must be None for mode \'{mode}\'')

		if data_mode == QSPIDataMode.x1:
			dq = dq.split(' ')
			if len(dq) != 3:
				raise ValueError(f'dq must have exactly 3 pins, not {len(dq)}')
			ios.append(Subsignal('copi', Pins(dq[0], dir = 'o', conn = conn)))
			ios.append(Subsignal('cipo', Pins(dq[1], dir = 'i', conn = conn)))
			ios.append(Subsignal('hold', PinsN(dq[2], dir = 'io', conn = conn)))
		elif data_mode == QSPIDataMode.x2:
			dq = dq.split(' ')
			if len(dq) != 3:
				raise ValueError(f'dq must have exactly 3 pins not {len(dq)}')
			ios.append(Subsignal('dq', Pins(f'{dq[0]} {dq[1]}', dir = 'io', conn = conn)))
			ios.append(Subsignal('hold', PinsN(dq[2], dir = 'io', conn = conn)))
		elif data_mode == QSPIDataMode.x4:
			ios.append(Subsignal('dq', Pins(dq, dir = 'io', conn = conn, assert_width = 4)))

	if clk_fb is not None:
		ios.append(Subsignal('clk_fb', Pins(clk_fb, dir = 'i', conn = conn, assert_width = 1)))
	if attrs is not None:
		ios.append(attrs)
	return Resource.family(name_or_number, number, default_name = 'qspi', ios = ios)

def SDCardResources(
	name_or_number: str | int, number: int | None = None, *,
	clk: str, cmd: str, dat0: str, dat1: str | None = None, dat2: str | None = None,
	dat3: str | None = None, cd: str | None = None, wp_n: str | None = None, det: str | None = None,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> list[Resource]:
	'''
	.. todo:: Document Me
	'''

	resources: list[Resource]   = []
	io_common: list[SubsigArgT] = []

	if attrs is not None:
		io_common.append(attrs)

	if cd is not None:
		io_common.append(Subsignal('cd', Pins(cd, dir = 'i', conn = conn, assert_width = 1)))

	if wp_n is not None:
		io_common.append(Subsignal('wp', PinsN(wp_n, dir = 'i', conn = conn, assert_width = 1)))

	if det is not None:
		io_common.append(Subsignal('det', Pins(det, dir = 'i', conn = conn, assert_width = 1)))

	io_native = list(io_common)
	io_native.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
	io_native.append(Subsignal('cmd', Pins(cmd, dir = 'o', conn = conn, assert_width = 1)))

	io_1bit = list(io_native)
	io_1bit.append(Subsignal('dat', Pins(dat0, dir = 'io', conn = conn, assert_width = 1)))

	if dat3 is not None:
		# DAT3 has a pullup and works as electronic card detect
		io_1bit.append(Subsignal('ecd', Pins(dat3, dir = 'i', conn = conn, assert_width = 1)))

	resources.append(Resource.family(
		name_or_number, number, default_name = 'sd_card', ios = io_1bit, name_suffix = '1bit'
	))

	if dat1 is not None and dat2 is not None and dat3 is not None:
		io_4bit = list(io_native)
		io_4bit.append(Subsignal(
			'dat', Pins(' '.join((dat0, dat1, dat2, dat3)), dir = 'io', conn = conn, assert_width = 4)
		))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'sd_card', ios = io_4bit, name_suffix = '4bit'
		))

	if dat3 is not None:
		io_spi = list(io_common)
		# DAT3/CS# has a pullup and doubles as electronic card detect
		io_spi.append(Subsignal('cs', PinsN(dat3, dir = 'io', conn = conn, assert_width = 1)))
		io_spi.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
		io_spi.append(Subsignal('copi', Pins(cmd, dir = 'o', conn = conn, assert_width = 1)))
		io_spi.append(Subsignal('cipo', Pins(dat0, dir = 'i', conn = conn, assert_width = 1)))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'sd_card', ios = io_spi, name_suffix = 'spi'
		))

	return resources

def SPIFlashResources(
	name_or_number: str | int, number: int | None = None, *,
	cs_n: str, clk: str, copi: str, cipo: str, wp_n: str | None = None,
	hold_n: str | None = None, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> list[Resource]:
	'''
	.. todo:: Document Me
	'''

	resources: list[Resource] = []
	io_all: list[SubsigArgT]  = []

	if attrs is not None:
		io_all.append(attrs)

	io_all.append(Subsignal('cs',  PinsN(cs_n, dir = 'o', conn = conn)))
	io_all.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))

	io_1x = list(io_all)
	io_1x.append(Subsignal('copi', Pins(copi, dir = 'o', conn = conn, assert_width = 1)))
	io_1x.append(Subsignal('cipo', Pins(cipo, dir = 'i', conn = conn, assert_width = 1)))

	if wp_n is not None and hold_n is not None:
		io_1x.append(Subsignal('wp',   PinsN(wp_n,   dir = 'o', conn = conn, assert_width = 1)))
		io_1x.append(Subsignal('hold', PinsN(hold_n, dir = 'o', conn = conn, assert_width = 1)))

	resources.append(Resource.family(
		name_or_number, number, default_name = 'spi_flash', ios = io_1x, name_suffix = '1x'
	))

	io_2x = list(io_all)
	io_2x.append(Subsignal(
		'dq', Pins(' '.join([copi, cipo]), dir = 'io', conn = conn, assert_width = 2)
	))
	resources.append(Resource.family(
		name_or_number, number, default_name = 'spi_flash', ios = io_2x, name_suffix = '2x'
	))

	if wp_n is not None and hold_n is not None:
		io_4x = list(io_all)
		io_4x.append(Subsignal(
			'dq', Pins(' '.join([copi, cipo, wp_n, hold_n]), dir = 'io', conn = conn, assert_width = 4)
		))
		resources.append(Resource.family(
			name_or_number, number, default_name = 'spi_flash', ios = io_4x, name_suffix = '4x'
		))

	return resources
