# SPDX-License-Identifier: BSD-2-Clause

from typing   import Optional, Tuple, Union

from ...build import *


__all__ = (
	'Display7SegResource',
	'VGAResource',
	'VGADACResource',
)


def Display7SegResource(
	*args,
	a : str, b : str, c : str, d : str, e : str, f : str, g : str, dp : Optional[str] = None,
	invert : bool = False, conn : Optional[Union[Tuple[str, int], str]] = None,
	attrs : Optional[Attrs] = None
) -> Resource:

	ios = []

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
	return Resource.family(*args, default_name = 'display_7seg', ios = ios)


def VGAResource(
	*args,
	r : str, g : str, b : str, vs : str, hs : str,
	invert_sync : bool = False, conn : Optional[Union[Tuple[str, int], str]] = None,
	attrs : Optional[Attrs] = None
) -> Resource:

	ios = []

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

	return Resource.family(*args, default_name = 'vga', ios = ios)


def VGADACResource(
	*args,
	clk : str, r : str, g : str, b : str, vs : str, hs : str, extras : list[Subsignal] = [],
	invert_sync : bool = False, conn : Optional[Union[Tuple[str, int], str]] = None,
	attrs : Optional[Attrs] = None
) -> Resource:

	ios = []

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

	return Resource.family(*args, default_name = 'vgadac', ios = ios)
