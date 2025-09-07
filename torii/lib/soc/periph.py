# SPDX-License-Identifier: BSD-2-Clause

from collections     import OrderedDict
from collections.abc import Generator, Mapping

from ...util.units   import bits_for
from ..mem.map       import MemoryMap
from .               import event

__all__ = (
	'ConstantBool',
	'ConstantInt',
	'ConstantMap',
	'ConstantValue',
	'PeripheralInfo',
)

class ConstantValue:
	'''
	.. todo:: Document Me
	'''

	pass

class ConstantBool(ConstantValue):
	'''
	Boolean constant.

	Parameters
	----------
	value: bool
		Constant value.
	'''

	def __init__(self, value: bool) -> None:
		if not isinstance(value, bool):
			raise TypeError(f'Value must be a bool, not {value!r}')
		self._value = value

	@property
	def value(self) -> bool:
		''' The value of this constant. '''

		return self._value

	def __repr__(self) -> str:
		return f'ConstantBool({self.value})'

class ConstantInt(ConstantValue):
	'''
	Integer constant.

	Parameters
	----------
	value: int
		Constant value.

	width: int | None
		Width of ``value`` in bits. If ``None`` it is calculated by using
		:py:meth:`bits_for <torii.util.units.bits_for>` to derive it from ``value``.

	signed: bool | None
		If the value is signed. If ``None`` this is determined by checking
		if ``value > 0``.
	'''

	def __init__(
		self, value: int, *, width: int | None = None, signed: bool | None = None
	) -> None:
		if not isinstance(value, int):
			raise TypeError(f'Value must be an integer, not {value!r}')
		self._value = value

		if width is None:
			width = bits_for(value)
		if not isinstance(width, int):
			raise TypeError(f'Width must be an integer, not {width!r}')
		if width < bits_for(value):
			raise ValueError(f'Width must be greater than or equal to the number of bits needed to represent {value}')
		self._width = width

		if signed is None:
			signed = value < 0
		if not isinstance(signed, bool):
			raise TypeError(f'Signedness must be a bool, not {signed!r}')
		self._signed = signed

	@property
	def value(self) -> int:
		''' The value of this constant. '''

		return self._value

	@property
	def width(self) -> int:
		''' The width in bits needed to represent this constant. '''

		return self._width

	@property
	def signed(self) -> bool:
		''' If the value in this constant is signed or not. '''

		return self._signed

	def __repr__(self) -> str:
		return f'ConstantInt({self.value}, width={self.width}, signed={self.signed})'

class ConstantMap(Mapping):
	'''
	Named constant map.

	A read-only container for named constants. Keys are iterated in insertion order.

	Parameters
	----------
	**constants: dict[str, ConstantValue]
		Named constants.

	Examples
	--------
	.. code-block:: pycon

		>>> ConstantMap(RX_FIFO_DEPTH = 16)
		ConstantMap([('RX_FIFO_DEPTH', ConstantInt(16, width = 5, signed = False))])
	'''

	def __init__(self, **constants: dict[str, ConstantValue]) -> None:
		self._storage = OrderedDict()
		for key, value in constants.items():
			if isinstance(value, bool):
				value = ConstantBool(value)
			if isinstance(value, int):
				value = ConstantInt(value)
			if not isinstance(value, ConstantValue):
				raise TypeError(f'Constant value must be an instance of ConstantValue, not {value!r}')
			self._storage[key] = value

	def __getitem__(self, key) -> ConstantValue:
		return self._storage[key]

	def __iter__(self) -> Generator[ConstantValue, None, None]:
		yield from self._storage

	def __len__(self) -> int:
		return len(self._storage)

	def __repr__(self) -> str:
		return f'ConstantMap({list(self._storage.items())})'

class PeripheralInfo:
	'''
	Peripheral metadata.

	A unified description of the local resources of a peripheral. It may be queried in order to
	recover its memory windows, CSR registers, event sources and configuration constants.

	Parameters
	----------
	memory_map: MemoryMap
		Memory map of the peripheral.

	irq: event.Source | None
		IRQ line of the peripheral.

	constant_map: ConstantMap | None
		Constant map of the peripheral.
	'''

	def __init__(
		self, *, memory_map: MemoryMap, irq: event.Source | None = None,
		constant_map: ConstantMap | None = None
	) -> None:
		if not isinstance(memory_map, MemoryMap):
			raise TypeError(f'Memory map must be an instance of MemoryMap, not {memory_map!r}')
		memory_map.freeze()
		self._memory_map = memory_map

		if irq is not None and not isinstance(irq, event.Source):
			raise TypeError(f'IRQ line must be an instance of event.Source, not {irq!r}')
		self._irq = irq

		if constant_map is None:
			constant_map = ConstantMap()
		if not isinstance(constant_map, ConstantMap):
			raise TypeError(f'Constant map must be an instance of ConstantMap, not {constant_map!r}')
		self._constant_map = constant_map

	@property
	def memory_map(self) -> MemoryMap:
		'''
		Memory map.

		Returns
		-------
		MemoryMap
			The memory map describing the local address space of the peripheral.
		'''

		return self._memory_map

	@property
	def irq(self) -> event.Source:
		'''
		IRQ line.

		Returns
		-------
		event.Source
			An event source used by the peripheral to request interrupts. If provided, its
			event map describes local events.

		Raises
		------
		NotImplementedError
			If peripheral info does not have an IRQ line.
		'''

		if self._irq is None:
			raise NotImplementedError('Peripheral info does not have an IRQ line')
		return self._irq

	@property
	def constant_map(self) -> ConstantMap:
		'''
		Constant map.

		Returns
		-------
		ConstantMap
			The map containing the configuration constants of the peripheral.
		'''

		return self._constant_map
