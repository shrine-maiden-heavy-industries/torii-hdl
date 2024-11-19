# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

from typing    import Literal

from ....      import Elaboratable, Module
from ....build import Platform
from ..        import event
from .         import Element, Multiplexer
from .bus      import Interface

__all__ = (
	'EventMonitor',
)


class EventMonitor(Elaboratable):
	'''
	Event monitor.

	A monitor for subordinate event sources, with a CSR bus interface.

	CSR registers
	-------------
	enable : ``self.src.event_map.size``, read/write
		Enabled events. See :meth:`..event.EventMap.sources` for layout.
	pending : ``self.src.event_map.size``, read/clear
		Pending events. See :meth:`..event.EventMap.sources` for layout.

	Parameters
	----------
	data_width : int
		CSR bus data width. See :class:`..csr.Interface`.
	alignment : int
		CSR address alignment. See :class:`..memory.MemoryMap`.
	trigger : :class:`..event.Source.Trigger`
		Trigger mode. See :class:`..event.Source`.

	'''

	def __init__(
		self, *, data_width: int, alignment: int = 0,
		trigger: event.Source.Trigger | Literal['level', 'rise', 'fall'] = 'level'
	) -> None:
		choices = ('level', 'rise', 'fall')
		if not isinstance(trigger, event.Source.Trigger) and trigger not in choices:
			raise ValueError(f'Invalid trigger mode {trigger!r}; must be one of {", ".join(choices)}')

		self._trigger                       = event.Source.Trigger(trigger)
		self._map                           = event.EventMap()
		self._monitor: event.Monitor | None = None
		self._enable: Element | None        = None
		self._pending: Element | None       = None
		self._mux                           = Multiplexer(addr_width = 1, data_width = data_width, alignment = alignment)
		self._frozen                        = False

	def freeze(self) -> None:
		'''
		Freeze the event monitor.

		Once the event monitor is frozen, subordinate sources cannot be added anymore.

		'''

		if self._frozen:
			return
		self._monitor = event.Monitor(self._map, trigger = self._trigger)
		self._enable  = Element(self._map.size, Element.Access.RW)
		self._pending = Element(self._map.size, Element.Access.RW)
		self._mux.add(self._enable,  extend = True)
		self._mux.add(self._pending, extend = True)
		self._frozen  = True

	@property
	def src(self) -> event.Source:
		'''
		Event source.

		Return value
		------------
		An :class:`..event.Source`. Its input line is asserted by the monitor when a subordinate
		event is enabled and pending.

		'''

		self.freeze()
		assert self._monitor is not None
		return self._monitor.src

	@property
	def bus(self) -> Interface:
		'''
		CSR bus interface.

		Return value
		------------
		A :class:`..csr.Interface` providing access to registers.

		'''

		self.freeze()
		return self._mux.bus

	def add(self, src: event.Source) -> None:
		'''
		Add a subordinate event source.

		See :meth:`..event.EventMap.add` for details.

		'''

		self._map.add(src)

	def elaborate(self, _: Platform | None) -> Module:
		self.freeze()
		assert self._monitor is not None
		assert self._enable is not None
		assert self._pending is not None

		m = Module()
		m.submodules.monitor = self._monitor
		m.submodules.mux     = self._mux

		with m.If(self._enable.w_stb):
			m.d.sync += self._monitor.enable.eq(self._enable.w_data)
		m.d.comb += self._enable.r_data.eq(self._monitor.enable)

		with m.If(self._pending.w_stb):
			m.d.comb += self._monitor.clear.eq(self._pending.w_data)
		m.d.comb += self._pending.r_data.eq(self._monitor.pending)

		return m
