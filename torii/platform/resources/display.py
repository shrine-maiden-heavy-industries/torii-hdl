# SPDX-License-Identifier: BSD-2-Clause

from ...build.dsl import Attrs, Pins, Resource, Subsignal, SubsigArgT, ResourceConn

__all__ = (
	'Display7SegResource',
	'VGADACResource',
	'VGAResource',
)


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
