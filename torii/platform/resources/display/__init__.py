# SPDX-License-Identifier: BSD-2-Clause

from ...._typing   import IODirectionIO
from ....build.dsl import Attrs, DiffPairs, Pins, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'Display7SegResource',
	'HDMIResource',
	'VGADACResource',
	'VGAResource',
)

# TODO(aki): Add optional enable signal
def Display7SegResource(
	name_or_number: str | int, number: int | None = None, *,
	a: str, b: str, c: str, d: str, e: str, f: str, g: str, dp: str | None = None,
	invert: bool = False, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	ios.append(Subsignal('a', Pins(a, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('c', Pins(c, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('d', Pins(d, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('e', Pins(e, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('f', Pins(f, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', invert = invert, conn = conn, assert_width = 1)))

	if dp is not None:
		ios.append(Subsignal(
			'dp', Pins(dp, dir = 'o', invert = invert, conn = conn, assert_width = 1)
		))

	if attrs is not None:
		ios.append(attrs)
	return Resource.family(name_or_number, number, default_name = 'display_7seg', ios = ios)

def HDMIResource(
	name_or_number: str | int, number: int | None = None, *,
	clk_p: str, clk_n: str, d_p: str, d_n: str, scl: str, sda: str,
	hpd: str | None = None, cec: str | None = None,
	dir: IODirectionIO = 'io',
	conn: ResourceConn | None = None, diff_attrs: Attrs = Attrs(), attrs: Attrs = Attrs()
):
	ios: list[SubsigArgT] = []

	match dir:
		case 'i':
			dir_in = 'i'
			dir_out = 'o'
		case 'o':
			dir_in = 'o'
			dir_out = 'i'
		case 'io':
			dir_in = 'io'
			dir_out = 'io'

	ios.append(Subsignal('clk', DiffPairs(clk_p, clk_n, dir = dir_in, conn = conn, assert_width = 1), diff_attrs))
	ios.append(Subsignal('d', DiffPairs(d_p, d_n, dir = dir_in, conn = conn, assert_width = 3), diff_attrs))
	if cec:
		ios.append(Subsignal('cec', Pins(cec, dir = 'io', conn = conn, assert_width = 1), attrs))
	if hpd:
		ios.append(Subsignal('hpd', Pins(hpd, dir = dir_out, conn = conn, assert_width = 1), attrs))
	ios.append(Subsignal('sda', Pins(sda, dir = 'io', conn = conn, assert_width = 1), attrs))
	ios.append(Subsignal('scl', Pins(scl, dir = 'io', conn = conn, assert_width = 1), attrs))

	return Resource.family(name_or_number, number, default_name = 'hdmi', ios = ios)

def VGADACResource(
	name_or_number: str | int, number: int | None = None, *,
	clk: str, r: str, g: str, b: str, vs: str, hs: str, extras: list[Subsignal] = [],
	invert_sync: bool = False, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	ios.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('r', Pins(r, dir = 'o', conn = conn)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', conn = conn)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', conn = conn)))
	ios.append(Subsignal(
		'hs', Pins(hs, dir = 'o', invert = invert_sync, conn = conn, assert_width = 1)
	))
	ios.append(Subsignal(
		'vs', Pins(vs, dir = 'o', invert = invert_sync, conn = conn, assert_width = 1)
	))
	for extra in extras:
		ios.append(extra)

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'vgadac', ios = ios)

def VGAResource(
	name_or_number: str | int, number: int | None = None, *,
	r: str, g: str, b: str, vs: str, hs: str,
	invert_sync: bool = False, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	ios.append(Subsignal('r', Pins(r, dir = 'o', conn = conn)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', conn = conn)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', conn = conn)))
	ios.append(Subsignal(
		'hs', Pins(hs, dir = 'o', invert = invert_sync, conn = conn, assert_width = 1)
	))
	ios.append(Subsignal(
		'vs', Pins(vs, dir = 'o', invert = invert_sync, conn = conn, assert_width = 1)
	))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'vga', ios = ios)
