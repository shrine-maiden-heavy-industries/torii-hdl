# SPDX-License-Identifier: BSD-2-Clause

from ....build.dsl import Attrs, DiffPairs, Pins, PinsN, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'DDR3Resource',
	'SDRAMResource',
	'SRAMResource',
)

# TODO(aki): Add DDR1/DDR2/DDR4/DDR5
def DDR3Resource(
	name_or_number: str | int, number: int | None = None, *,
	rst_n: str | None = None,
	clk_p: str, clk_n: str, clk_en: str, cs_n: str, we_n: str, ras_n: str, cas_n: str,
	a: str, ba: str, dqs_p: str, dqs_n: str, dq: str, dm: str, odt: str,
	conn: ResourceConn | None = None,
	diff_attrs = None, attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	if rst_n is not None:
		ios.append(Subsignal('rst', PinsN(rst_n, dir = 'o', conn = conn, assert_width = 1)))

	ios.append(Subsignal('clk', DiffPairs(clk_p, clk_n, dir = 'o', conn = conn, assert_width = 1), diff_attrs))
	ios.append(Subsignal('clk_en', Pins(clk_en, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('we', PinsN(we_n, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('ras', PinsN(ras_n, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('cas', PinsN(cas_n, dir = 'o', conn = conn, assert_width = 1)))
	ios.append(Subsignal('a', Pins(a, dir = 'o', conn = conn)))
	ios.append(Subsignal('ba', Pins(ba, dir = 'o', conn = conn)))
	ios.append(Subsignal('dqs', DiffPairs(dqs_p, dqs_n, dir = 'io', conn = conn), diff_attrs))
	ios.append(Subsignal('dq', Pins(dq, dir = 'io', conn = conn)))
	ios.append(Subsignal('dm', Pins(dm, dir = 'o', conn = conn)))
	ios.append(Subsignal('odt', Pins(odt, dir = 'o', conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'ddr3', ios = ios)

def SDRAMResource(
	name_or_number: str | int, number: int | None = None, *,
	clk: str, cke: str | None = None, cs_n: str | None = None,
	we_n: str, ras_n: str, cas_n: str, ba: str, a: str, dq: str,
	dqm: str | None = None, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	io: list[SubsigArgT] = []

	io.append(Subsignal('clk', Pins(clk, dir = 'o', conn = conn, assert_width = 1)))
	if cke is not None:
		io.append(Subsignal('clk_en', Pins(cke, dir = 'o', conn = conn, assert_width = 1)))

	if cs_n is not None:
		io.append(Subsignal('cs', PinsN(cs_n,  dir = 'o', conn = conn, assert_width = 1)))

	io.append(Subsignal('we',  PinsN(we_n,  dir = 'o', conn = conn, assert_width = 1)))
	io.append(Subsignal('ras', PinsN(ras_n, dir = 'o', conn = conn, assert_width = 1)))
	io.append(Subsignal('cas', PinsN(cas_n, dir = 'o', conn = conn, assert_width = 1)))
	io.append(Subsignal('ba', Pins(ba, dir = 'o', conn = conn)))
	io.append(Subsignal('a',  Pins(a,  dir = 'o', conn = conn)))
	io.append(Subsignal('dq', Pins(dq, dir = 'io', conn = conn)))

	if dqm is not None:
		io.append(Subsignal('dqm', Pins(dqm, dir = 'o', conn = conn))) # dqm = 'LDQM# UDQM#'

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'sdram', ios = io)

def SRAMResource(
	name_or_number: str | int, number: int | None = None, *,
	cs_n: str, oe_n: str | None = None, we_n: str, a: str, d: str,
	dm_n: str | None = None, conn: ResourceConn | None = None,
	attrs: Attrs | None = None
) -> Resource:
	io: list[SubsigArgT] = []

	io.append(Subsignal('cs', PinsN(cs_n, dir = 'o', conn = conn, assert_width = 1)))

	if oe_n is not None:
		# Asserted WE# deactivates the D output buffers, so WE# can be used to replace OE#.
		io.append(Subsignal('oe', PinsN(oe_n, dir = 'o', conn = conn, assert_width = 1)))

	io.append(Subsignal('we', PinsN(we_n, dir = 'o', conn = conn, assert_width = 1)))
	io.append(Subsignal('a', Pins(a, dir = 'o', conn = conn)))
	io.append(Subsignal('d', Pins(d, dir = 'io', conn = conn)))

	if dm_n is not None:
		io.append(Subsignal('dm', PinsN(dm_n, dir = 'o', conn = conn))) # dm = 'LB# UB#'

	if attrs is not None:
		io.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'sram', ios = io)
