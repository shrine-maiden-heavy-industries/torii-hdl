# SPDX-License-Identifier: BSD-2-Clause

from ....hdl.ast     import Cat, Signal
from ....hdl.dsl     import Module
from ....hdl.ir      import Elaboratable
from ....util.units  import log2_exact
from ...bus.wishbone import Interface as WishboneInterface
from ...mem.map      import MemoryMap
from .               import Interface as CSRInterface

__all__ = (
	'WishboneCSRBridge',
)

class WishboneCSRBridge(Elaboratable):
	'''
	Wishbone to CSR bridge.

	A bus bridge for accessing CSR registers from Wishbone. This bridge supports any Wishbone
	data width greater or equal to CSR data width and performs appropriate address translation.

	Latency
	-------

	Reads and writes always take ``self.data_width // csr_bus.data_width + 1`` cycles to complete,
	regardless of the select inputs. Write side effects occur simultaneously with acknowledgement.

	Parameters
	----------
	csr_bus : :class:`..csr.Interface`
		CSR bus driven by the bridge.
	data_width : int or None
		Wishbone bus data width. If not specified, defaults to ``csr_bus.data_width``.
	name : str
		Window name. Optional.

	Attributes
	----------
	wb_bus : :class:`...bus.wishbone.Interface`
		Wishbone bus provided by the bridge.

	'''

	def __init__(
		self, csr_bus: CSRInterface, *, data_width: int | None = None, name: str | None = None
	) -> None:
		if not isinstance(csr_bus, CSRInterface):
			raise ValueError(f'CSR bus must be an instance of CSRInterface, not {csr_bus!r}')
		if csr_bus.data_width not in (8, 16, 32, 64):
			raise ValueError(f'CSR bus data width must be one of 8, 16, 32, 64, not {csr_bus.data_width!r}')
		if data_width is None:
			data_width = csr_bus.data_width

		self.csr_bus = csr_bus
		self.wb_bus  = WishboneInterface(
			addr_width = max(0, csr_bus.addr_width - log2_exact(data_width // csr_bus.data_width)),
			data_width = data_width,
			granularity = csr_bus.data_width,
			name = 'wb'
		)

		wb_map = MemoryMap(
			addr_width = csr_bus.addr_width,
			data_width = csr_bus.data_width,
			name = name
		)
		# Since granularity of the Wishbone interface matches the data width of the CSR bus,
		# no width conversion is performed, even if the Wishbone data width is greater.
		wb_map.add_window(self.csr_bus.memory_map)
		self.wb_bus.memory_map = wb_map

	def elaborate(self, platform) -> Module:
		csr_bus = self.csr_bus
		wb_bus  = self.wb_bus

		m = Module()

		cycle = Signal(range(len(wb_bus.sel) + 1))
		m.d.comb += csr_bus.addr.eq(Cat(cycle[:log2_exact(len(wb_bus.sel))], wb_bus.adr))

		with m.If(wb_bus.cyc & wb_bus.stb):
			with m.Switch(cycle):
				def segment(index):
					return slice(index * wb_bus.granularity, (index + 1) * wb_bus.granularity)

				for index, sel_index in enumerate(wb_bus.sel):
					with m.Case(index):
						if index > 0:
							# CSR reads are registered, and we need to re-register them.
							m.d.sync += wb_bus.dat_r[segment(index - 1)].eq(csr_bus.r_data)
						m.d.comb += csr_bus.r_stb.eq(sel_index & ~wb_bus.we)
						m.d.comb += csr_bus.w_data.eq(wb_bus.dat_w[segment(index)])
						m.d.comb += csr_bus.w_stb.eq(sel_index & wb_bus.we)
						m.d.sync += cycle.eq(index + 1)

				with m.Default():
					m.d.sync += wb_bus.dat_r[segment(index)].eq(csr_bus.r_data)
					m.d.sync += wb_bus.ack.eq(1)

		with m.If(wb_bus.ack):
			m.d.sync += cycle.eq(0)
			m.d.sync += wb_bus.ack.eq(0)

		return m
