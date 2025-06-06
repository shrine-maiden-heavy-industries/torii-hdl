# SPDX-License-Identifier: BSD-2-Clause

from __future__      import annotations

import operator
from collections     import OrderedDict
from collections.abc import Sequence

from ..util          import tracer
from .ast            import Array, Cat, Const, Mux, Signal, Switch
from .ir             import Elaboratable, Fragment

__all__ = (
	'DummyPort',
	'Memory',
	'ReadPort',
	'WritePort',
)

class Memory(Elaboratable):
	'''
	A word addressable storage.

	Parameters
	----------
	width : int
		Access granularity. Each storage element of this memory is ``width`` bits in size.

	depth : int
		Word count. This memory contains ``depth`` storage elements.

	init : Sequence[int]
		Initial values. At power on, each storage element in this memory is initialized to
		the corresponding element of ``init``, if any, or to zero otherwise.
		Uninitialized memories are not currently supported.

	name : str | None
		Name hint for this memory. If ``None`` the name is inferred from the variable
		name this ``Memory`` is assigned to.
		(default: None)

	attrs : dict | None
		Dictionary of synthesis attributes.
		(default: None)

	Attributes
	----------
	width : int
		Width of each element in this memory.

	depth : int
		Number of elements in this memory.

	init : list of int
		Initial values for this memory.

	attrs : dict
		Synthesis attributes.

	'''

	def __init__(
		self, *, width: int, depth: int, init: Sequence[int] | None = None, name: str | None = None,
		attrs: OrderedDict | None = None, simulate: bool = True
	) -> None:
		if not isinstance(width, int) or width < 0:
			raise TypeError(f'Memory width must be a non-negative integer, not {width!r}')
		if not isinstance(depth, int) or depth < 0:
			raise TypeError(f'Memory depth must be a non-negative integer, not {depth!r}')

		self.name    = name or tracer.get_var_name(depth = 2, default = '$memory')
		self.src_loc = tracer.get_src_loc()

		self.width = width
		self.depth = depth
		self.attrs = OrderedDict(() if attrs is None else attrs)

		# Array of signals for simulation.
		self._array = Array()
		if simulate:
			for addr in range(self.depth):
				self._array.append(Signal(self.width, name = f'{name or "memory"}({addr})'))

		self.init = init
		self._read_ports: list[ReadPort] = []
		self._write_ports: list[WritePort] = []

	@property
	def init(self):
		return self._init

	@init.setter
	def init(self, new_init):
		self._init = [] if new_init is None else list(new_init)
		if len(self.init) > self.depth:
			raise ValueError(f'Memory initialization value count exceed memory depth ({len(self.init)} > {self.depth})')

		try:
			for addr in range(len(self._array)):
				if addr < len(self._init):
					self._array[addr].reset = operator.index(self._init[addr])
				else:
					self._array[addr].reset = 0
		except TypeError as e:
			raise TypeError(f'Memory initialization value at address {addr:x}: {e}') from None

	def read_port(self, *, domain: str = 'sync', transparent: bool = True, src_loc_at: int = 0) -> ReadPort:
		'''
		Get an instance of :py:class:`ReadPort` that is associated with this memory.

		See :py:class:`ReadPort` for details.

		Arguments
		---------
		domain : str
			The domain this :py:class:`ReadPort` operates on.
			(default: 'sync')

		transparent : bool
			Port transparency.
			(default: True)

		Returns
		-------
		An instance of :py:class:`ReadPort` associated with this memory.

		'''

		return ReadPort(self, domain = domain, transparent = transparent, src_loc_at = 1 + src_loc_at)

	def write_port(self, *, domain: str = 'sync', granularity: int | None = None, src_loc_at: int = 0) -> WritePort:
		'''
		Get an instance of :py:class:`WritePort` that is associated with this memory.

		See :py:class:`WritePort` for details.

		Arguments
		---------
		domain : str
			The domain this :py:class:`WritePort` operates on.
			(default: 'sync')

		granularity : int | None
			Port granularity
			(default: None)

		Returns
		-------
		An instance of :py:class:`WritePort` associated with this memory.

		'''

		return WritePort(self, domain = domain, granularity = granularity, src_loc_at = 1 + src_loc_at)

	def __getitem__(self, index):
		''' Simulation only. '''
		return self._array[index]

	def elaborate(self, platform):
		f = MemoryInstance(self, self._read_ports, self._write_ports)

		for port in self._read_ports:
			port._MustUse__used = True
			if port.domain == 'comb':
				f.add_statements(port.data.eq(self._array[port.addr]))
				f.add_driver(port.data)
			else:
				data = self._array[port.addr]
				for write_port in self._write_ports:
					if port.domain == write_port.domain and port.transparent:
						if len(write_port.en) > 1:
							parts = []
							for index, en_bit in enumerate(write_port.en):
								offset = index * write_port.granularity
								bits = slice(offset, offset + write_port.granularity)
								cond = en_bit & (port.addr == write_port.addr)
								parts.append(Mux(cond, write_port.data[bits], data[bits]))
							data = Cat(parts)
						else:
							cond = write_port.en & (port.addr == write_port.addr)
							data = Mux(cond, write_port.data, data)
				f.add_statements(
					Switch(port.en, {
						1: port.data.eq(data)
					})
				)
				f.add_driver(port.data, port.domain)
		for port in self._write_ports:
			port._MustUse__used = True
			if len(port.en) > 1:
				for index, en_bit in enumerate(port.en):
					offset = index * port.granularity
					bits   = slice(offset, offset + port.granularity)
					write_data = self._array[port.addr][bits].eq(port.data[bits])
					f.add_statements(Switch(en_bit, { 1: write_data }))
			else:
				write_data = self._array[port.addr].eq(port.data)
				f.add_statements(Switch(port.en, { 1: write_data }))
			for signal in self._array:
				f.add_driver(signal, port.domain)
		return f

class ReadPort(Elaboratable):
	'''
	A memory read port.

	Parameters
	----------
	memory : Memory
		Memory associated with the port.

	domain : str
		The clock domain this port operates on. If set to the ``'comb'`` domain, the port is
		asynchronous, otherwise reads have a latency of 1 clock cycle.
		(default: ``'sync'``)

	transparent : bool
		Port transparency. If set a read at an address that is also being written to in
		the same clock cycle will output the new value. Otherwise, the old value will be output
		first. This behavior only applies to ports in the same domain.
		(default: True)

	Attributes
	----------
	memory : Memory
		The memory associated to this port.

	domain : str
		The clock domain this port operates on.

	transparent : bool
		If port transparency is enabled.

	addr : Signal(range(memory.depth)), in
		Read address.

	data : Signal(memory.width), out
		Read data.

	en : Signal or Const, in
		Read enable. If asserted, ``data`` is updated with the word stored at ``addr``.

	Raises
	------
	:class:`ValueError` if the read port is simultaneously asynchronous and non-transparent.

	'''

	def __init__(self, memory: Memory, *, domain: str = 'sync', transparent: bool = True, src_loc_at: int = 0):
		if domain == 'comb' and not transparent:
			raise ValueError('Read port cannot be simultaneously asynchronous and non-transparent')

		self.memory      = memory
		self.domain      = domain
		self.transparent = transparent

		self.addr = Signal(
			range(memory.depth),
			name = f'{memory.name}_r_addr', src_loc_at = 1 + src_loc_at
		)
		self.data = Signal(
			memory.width,
			name = f'{memory.name}_r_data', src_loc_at = 1 + src_loc_at
		)
		if self.domain != 'comb':
			self.en = Signal(
				name = f'{memory.name}_r_en', reset = 1,
				src_loc_at = 1 + src_loc_at
			)
		else:
			self.en = Const(1)

		memory._read_ports.append(self)

	def elaborate(self, platform):
		if self is self.memory._read_ports[0]:
			return self.memory
		else:
			return Fragment()

class WritePort(Elaboratable):
	'''
	A memory write port.

	Parameters
	----------
	memory : Memory
		Memory associated with the port.

	domain : str
		The clock domain this port operates on. Writes have a latency of 1 clock cycle.
		(default: ``'sync'``)

	granularity : int | None
		Port granularity. Write data is split evenly in ``memory.width // granularity`` chunks,
		which can be updated independently. If ``None`` defaults to ``memory.width``.
		(default: None)

	Attributes
	----------
	memory : Memory
		The memory associated to this port.

	domain : str
		The clock domain this port operates on.

	granularity : int
		The port granularity.

	addr : Signal(range(memory.depth)), in
		Write address.

	data : Signal(memory.width), in
		Write data.

	en : Signal(memory.width // granularity), in
		Write enable. Each bit selects a non-overlapping chunk of ``granularity`` bits on the
		``data`` signal, which is written to memory at ``addr``. Unselected chunks are ignored.

	Raises
	------
	:class:`ValueError` if the write port granularity is greater than memory width, or does not
	divide memory width evenly.

	'''

	def __init__(self, memory: Memory, *, domain: str = 'sync', granularity: int | None = None, src_loc_at: int = 0):
		if granularity is None:
			granularity = memory.width
		if not isinstance(granularity, int) or granularity < 0:
			raise TypeError(f'Write port granularity must be a non-negative integer, not {granularity!r}')
		if granularity > memory.width:
			raise ValueError(f'Write port granularity must not be greater than memory width ({granularity} > {memory.width})')
		if memory.width // granularity * granularity != memory.width:
			raise ValueError('Write port granularity must divide memory width evenly')

		self.memory       = memory
		self.domain       = domain
		self.granularity  = granularity

		self.addr = Signal(
			range(memory.depth),
			name = f'{memory.name}_w_addr', src_loc_at = 1 + src_loc_at
		)
		self.data = Signal(
			memory.width,
			name = f'{memory.name}_w_data', src_loc_at = 1 + src_loc_at
		)
		self.en   = Signal(
			memory.width // granularity,
			name = f'{memory.name}_w_en', src_loc_at = 1 + src_loc_at
		)

		memory._write_ports.append(self)

	def elaborate(self, platform):
		if not self.memory._read_ports and self is self.memory._write_ports[0]:
			return self.memory
		else:
			return Fragment()

class DummyPort:
	'''
	Dummy memory port.

	This port can be used in place of either a read or a write port for testing and verification.
	It does not include any read/write port specific attributes, i.e. none besides ``'domain'``;
	any such attributes may be set manually.

	Parameters
	----------
	data_width : int
		The width of the ``data`` signal on this port.

	addr_width : int
		The width of the ``addr`` signal on this port.

	domain : str
		The domain this port is to operate on.
		(default: 'sync')

	name : str | None
		The name of this port.
		(default: None)

	granularity : str | None
		Port granularity if set. If ``None`` defaults to ``data_width``.
		(default: None)

	Attributes
	----------
	domain : str
		Port domain.

	addr : Signal(addr_width)
		Port address.

	data : Signal(data_width)
		Port data.

	en : Signal(data_width // granularity)
		Port enable bitmask.
	'''

	def __init__(
		self, *, data_width: int, addr_width: int, domain: str = 'sync', name: str | None = None,
		granularity: int | None = None
	):
		self.domain = domain

		if granularity is None:
			granularity = data_width
		if name is None:
			name = tracer.get_var_name(depth = 2, default = 'dummy')

		self.addr = Signal(addr_width, name = f'{name}_addr', src_loc_at = 1)
		self.data = Signal(data_width, name = f'{name}_data', src_loc_at = 1)
		self.en   = Signal(data_width // granularity, name = f'{name}_en', src_loc_at = 1)

class MemoryInstance(Fragment):
	def __init__(self, memory: Memory, read_ports: list[ReadPort], write_ports: list[WritePort]):
		super().__init__()
		self.memory      = memory
		self.read_ports  = read_ports
		self.write_ports = write_ports
		self.attrs       = memory.attrs
