# SPDX-License-Identifier: BSD-2-Clause

from bisect        import bisect_left, bisect_right
from typing        import Generator, Iterable, List, Optional, Tuple, Union

from ...util.units import bits_for

__all__ = (
	'ResourceInfo',
	'MemoryMap',
)

class _RangeMap:
	'''Range map.

	A range map is a mapping from non-overlapping ranges to arbitrary values.
	'''
	def __init__(self) -> None:
		self._keys   = []
		self._values = dict()
		self._starts = []
		self._stops  = []

	def insert(self, key : range, value : object):
		assert isinstance(key, range)
		assert not self.overlaps(key)

		start_idx = bisect_right(self._starts, key.start)
		stop_idx  = bisect_left(self._stops, key.stop)
		assert start_idx == stop_idx

		self._starts.insert(start_idx, key.start)
		self._stops.insert(stop_idx, key.stop)
		self._keys.insert(start_idx, key)
		self._values[key] = value

	def get(self, point : int) -> object:
		point_idx = bisect_right(self._stops, point)
		if point_idx < len(self._keys):
			point_range = self._keys[point_idx]
			if point >= point_range.start and point < point_range.stop:
				return self._values[point_range]

	def overlaps(self, key : range) -> List[object]:
		start_idx = bisect_right(self._stops, key.start)
		stop_idx  = bisect_left(self._starts, key.stop)
		return [self._values[key] for key in self._keys[start_idx:stop_idx]]

	def items(self) -> Generator[Tuple[range, object], None, None]:
		for key in self._keys:
			yield (key, self._values[key])


class ResourceInfo:
	'''Resource metadata.

	A wrapper class for resource objects, with their assigned name and address range.

	Parameters
	----------
	resource : object
		Arbitrary object representing a resource. See :meth:`MemoryMap.add_resource` for details.
	name : iter(str)
		Name assigned to the resource. It is prefixed by the name of each window sitting between
		the resource and the memory map from which this :class:`ResourceInfo` was obtained.
		See :meth:`MemoryMap.add_window` for details.
	start : int
		Start of the address range assigned to the resource.
	end : int
		End of the address range assigned to the resource.
	width : int
		Amount of data bits accessed at each address. It may be equal to the data width of the
		memory map from which this :class:`ResourceInfo` was obtained, or less if the resource
		is located behind a window that uses sparse addressing.
	'''
	def __init__(
		self, resource : object, name : Union[str, Iterable[str]], start : int, end : int, width : int
	) -> None:
		if isinstance(name, str):
			name = (name,)
		if not name or not all(isinstance(part, str) and part for part in name):
			raise TypeError(f'Name must be a non-empty sequence of non-empty strings, not {name!r}')
		if not isinstance(start, int) or start < 0:
			raise TypeError(f'Start address must be a non-negative integer, not {start!r}')
		if not isinstance(end, int) or end <= start:
			raise TypeError(f'End address must be an integer greater than the start address, not {end!r}')
		if not isinstance(width, int) or width < 0:
			raise TypeError(f'Width must be a non-negative integer, not {width!r}')

		self._resource = resource
		self._name     = tuple(name)
		self._start    = start
		self._end      = end
		self._width    = width

	@property
	def resource(self) -> object:
		return self._resource

	@property
	def name(self) -> Tuple[str]:
		return self._name

	@property
	def start(self) -> int:
		return self._start

	@property
	def end(self) -> int:
		return self._end

	@property
	def width(self) -> int:
		return self._width


class MemoryMap:
	'''Memory map.

	A memory map is a hierarchical description of an address space, describing the structure of
	address decoders of peripherals as well as bus bridges. It is built by adding resources
	(range allocations for registers, memory, etc) and windows (range allocations for bus bridges),
	and can be queried later to determine the address of any given resource from a specific
	vantage point in the design.

	Address assignment
	------------------

	To simplify address assignment, each memory map has an implicit next address, starting at 0.
	If a resource or a window is added without specifying an address explicitly, the implicit next
	address is used. In any case, the implicit next address is set to the address immediately
	following the newly added resource or window.

	Parameters
	----------
	addr_width : int
		Address width.
	data_width : int
		Data width.
	alignment : log2 of int
		Range alignment. Each added resource and window will be placed at an address that is
		a multiple of ``2 ** alignment``, and its size will be rounded up to be a multiple of
		``2 ** alignment``.
	name : str
		Name of the address range. Optional.
	'''
	def __init__(
		self, *, addr_width : int, data_width : int, alignment : int = 0, name : Optional[str] = None
	) -> None:
		if not isinstance(addr_width, int) or addr_width <= 0:
			raise ValueError(f'Address width must be a positive integer, not {addr_width!r}')
		if not isinstance(data_width, int) or data_width <= 0:
			raise ValueError(f'Data width must be a positive integer, not {data_width!r}')
		if not isinstance(alignment, int) or alignment < 0:
			raise ValueError(f'Alignment must be a non-negative integer, not {alignment!r}')
		if name is not None and not (isinstance(name, str) and name):
			raise ValueError(f'Name must be a non-empty string, not {name!r}')

		self._addr_width = addr_width
		self._data_width = data_width
		self._alignment  = alignment
		self._name       = name

		self._ranges     = _RangeMap()
		self._resources  = dict()
		self._windows    = dict()
		self._namespace  = dict()

		self._next_addr  = 0
		self._frozen     = False

	@property
	def addr_width(self) -> int:
		return self._addr_width

	@addr_width.setter
	def addr_width(self, addr_width : int) -> None:
		if self._frozen:
			raise ValueError('Memory map has been frozen. Address width cannot be extended further')
		if not isinstance(addr_width, int) or addr_width <= 0:
			raise ValueError(f'Address width must be a positive integer, not {addr_width!r}')
		if addr_width < self._addr_width:
			raise ValueError(
				f'Address width {addr_width!r} must not be less than its previous value {self._addr_width!r}, '
				'because resources that were previously added may not fit anymore'
			)
		self._addr_width = addr_width

	@property
	def data_width(self) -> int:
		return self._data_width

	@property
	def alignment(self) -> int:
		return self._alignment

	@property
	def name(self) -> Optional[str]:
		return self._name

	def freeze(self) -> None:
		'''Freeze the memory map.

		Once the memory map is frozen, its visible state becomes immutable. Resources and windows
		cannot be added anymore, and its address width cannot be extended further.
		'''
		self._frozen = True

	@staticmethod
	def _align_up(value : int, alignment : int) -> int:
		if value % (1 << alignment) != 0:
			value += (1 << alignment) - (value % (1 << alignment))
		return value

	def align_to(self, alignment : int) -> int:
		'''Align the implicit next address.

		Arguments
		---------
		alignment : log2 of int
			Address alignment. The start of the implicit next address will be a multiple of
			``2 ** max(alignment, self.alignment)``.

		Return value
		------------
		Implicit next address.
		'''
		if not isinstance(alignment, int) or alignment < 0:
			raise ValueError(f'Alignment must be a non-negative integer, not {alignment!r}')
		self._next_addr = self._align_up(self._next_addr, max(alignment, self.alignment))
		return self._next_addr

	def _compute_addr_range(
		self, addr : int, size : int, step : int = 1, *, alignment : int, extend : bool
	) -> range:
		if addr is not None:
			if not isinstance(addr, int) or addr < 0:
				raise ValueError(f'Address must be a non-negative integer, not {addr!r}')
			if addr % (1 << self.alignment) != 0:
				raise ValueError(f'Explicitly specified address {addr:#x} must be a multiple of {1 << alignment:#x} bytes')
		else:
			addr = self._align_up(self._next_addr, alignment)

		if not isinstance(size, int) or size < 0:
			raise ValueError(f'Size must be a non-negative integer, not {size!r}')
		size = self._align_up(max(size, 1), alignment)

		if addr > (1 << self.addr_width) or addr + size > (1 << self.addr_width):
			if extend:
				self.addr_width = bits_for(addr + size)
			else:
				raise ValueError(
					f'Address range {addr:#x}..{addr + size:#x} out of bounds for memory map spanning '
					f'range {0:#x}..{1 << self.addr_width:#x} ({self.addr_width} address bits)'
				)

		addr_range = range(addr, addr + size, step)
		overlaps = self._ranges.overlaps(addr_range)
		if overlaps:
			overlap_descrs = []
			for overlap in overlaps:
				if id(overlap) in self._resources:
					_, _, resource_range = self._resources[id(overlap)]
					overlap_descrs.append(f'resource {overlap!r} at {resource_range.start:#x}..{resource_range.stop:#x}')
				if id(overlap) in self._windows:
					_, window_range = self._windows[id(overlap)]
					overlap_descrs.append(f'window {overlap!r} at {window_range.start:#x}..{ window_range.stop:#x}')
			raise ValueError(f'Address range {addr:#x}..{addr + size:#x} overlaps with {", ".join(overlap_descrs)}')

		return addr_range

	def add_resource(
		self, resource : object, *, name : str, size : int, addr : Optional[int] = None,
		alignment : Optional[int] = None, extend : bool = False
	) -> Tuple[int, int]:
		'''Add a resource.

		A resource is any device on the bus that is a destination for bus transactions, e.g.
		a register or a memory block.

		Arguments
		---------
		resource : object
			Arbitrary object representing a resource.
		name : str
			Name of the resource. It must not collide with the name of other resources or windows
			present in this memory map.
		addr : int or None
			Address of the resource. If ``None``, the implicit next address will be used.
			Otherwise, the exact specified address (which must be a multiple of
			``2 ** max(alignment, self.alignment)``) will be used.
		size : int
			Size of the resource, in minimal addressable units. Rounded up to a multiple of
			``2 ** max(alignment, self.alignment)``.
		alignment : log2 of int or None
			Alignment of the resource. If not specified, the memory map alignment is used.
		extend: bool
			Allow memory map extension. If ``True``, the upper bound of the address space is
			raised as needed, in order to fit a resource that would otherwise be out of bounds.

		Return value
		------------
		A tuple ``(start, end)`` describing the address range assigned to the resource.

		Exceptions
		----------
		Raises :exn:`ValueError` if one of the following occurs:

		- this memory map is frozen;
		- the requested address and size, after alignment, would overlap with any resources or
		windows that have already been added, or would be out of bounds;
		- the resource has already been added to this memory map;
		- the name of the resource is already present in the namespace of this memory map;
		'''
		if self._frozen:
			raise ValueError(f'Memory map has been frozen. Cannot add resource {resource!r}')

		if id(resource) in self._resources:
			_, _, addr_range = self._resources[id(resource)]
			raise ValueError(f'Resource {resource!r} is already added at address range {addr_range.start:#x}..{addr_range.stop:#x}')

		if not isinstance(name, str) or not name:
			raise TypeError(f'Name must be a non-empty string, not {name!r}')
		if name in self._namespace:
			raise ValueError(f'Name {name} is already used by {self._namespace[name]!r}')

		if alignment is not None:
			if not isinstance(alignment, int) or alignment < 0:
				raise ValueError(f'Alignment must be a non-negative integer, not {alignment!r}')
			alignment = max(alignment, self.alignment)
		else:
			alignment = self.alignment

		addr_range = self._compute_addr_range(addr, size, alignment = alignment, extend = extend)
		self._ranges.insert(addr_range, resource)
		self._resources[id(resource)] = resource, name, addr_range
		self._namespace[name] = resource
		self._next_addr = addr_range.stop
		return (addr_range.start, addr_range.stop)

	def resources(self):
		'''Iterate local resources and their address ranges.

		Non-recursively iterate resources in ascending order of their address.

		Yield values
		------------
		A tuple ``resource, name, (start, end)`` describing the address range assigned to the
		resource.
		'''
		for resource, resource_name, resource_range in self._resources.values():
			yield (resource, resource_name, (resource_range.start, resource_range.stop))

	def add_window(
		self, window : 'MemoryMap', *, addr : Optional[int] = None, sparse : Optional[int] = None,
		extend : bool = False
	) -> Tuple[int, int, int]:
		'''Add a window.

		A window is a device on a bus that provides access to a different bus, i.e. a bus bridge.
		It performs address translation, such that the devices on a subordinate bus have different
		addresses; the memory map reflects this address translation when resources are looked up
		through the window.

		Sparse addressing
		-----------------

		If a narrow bus is bridged to a wide bus, the bridge can perform *sparse* or *dense*
		address translation. In the sparse case, each transaction on the wide bus results in
		one transaction on the narrow bus; high data bits on the wide bus are ignored, and any
		contiguous resource on the narrow bus becomes discontiguous on the wide bus. In the dense
		case, each transaction on the wide bus results in several transactions on the narrow bus,
		and any contiguous resource on the narrow bus stays contiguous on the wide bus.

		Arguments
		---------
		window : :class:`MemoryMap`
			A memory map describing the layout of the window. It is frozen as a side-effect of
			being added to this memory map.
		addr : int or None
			Address of the window. If ``None``, the implicit next address will be used after
			aligning it to ``2 ** window.addr_width``. Otherwise, the exact specified address
			(which must be a multiple of ``2 ** window.addr_width``) will be used.
		sparse : bool or None
			Address translation type. Ignored if the datapath widths of both memory maps are
			equal; must be specified otherwise.
		extend : bool
			Allow memory map extension. If ``True``, the upper bound of the address space is
			raised as needed, in order to fit a window that would otherwise be out of bounds.

		Return value
		------------
		A tuple ``(start, end, ratio)`` describing the address range assigned to the window.
		When bridging buses of unequal data width, ``ratio`` is the amount of contiguous addresses
		on the narrower bus that are accessed for each transaction on the wider bus. Otherwise,
		it is always 1.

		Exceptions
		----------
		Raises :exn:`ValueError` if one of the following occurs:

		- this memory map is frozen;
		- the requested address and size, after alignment, would overlap with any resources or
		windows that have already been added, or would be out of bounds;
		- the added memory map has a wider datapath than this memory map;
		- dense address translation is used and the datapath width of this memory map is not an
		integer multiple of the datapath of the added memory map;
		- the name of the added memory map is already present in the namespace of this memory map;
		- the added memory map has no name, and the name of one of its subordinate resources or
		windows is already present in the namespace of this memory map;
		'''
		if not isinstance(window, MemoryMap):
			raise TypeError(f'Window must be a MemoryMap, not {window!r}')

		if self._frozen:
			raise ValueError(f'Memory map has been frozen. Cannot add window {window!r}')

		if id(window) in self._windows:
			_, addr_range = self._windows[id(window)]
			raise ValueError(f'Window {window!r} is already added at address range {addr_range.start:#x}..{addr_range.stop:#x}')

		if window.data_width > self.data_width:
			raise ValueError(
				f'Window has data width {window.data_width}, and cannot be added to a memory map '
				f'with data width {self.data_width}'
			)
		if window.data_width != self.data_width:
			if sparse is None:
				raise ValueError(
					'Address translation mode must be explicitly specified '
					f'when adding a window with data width {window.data_width} to a memory map '
					f'with data width {self.data_width}'
				)
			if not sparse and self.data_width % window.data_width != 0:
				raise ValueError(
					'Dense addressing cannot be used because the memory map '
					f'data width {self.data_width} is not an integer multiple of window '
					f'data width {window.data_width}'
				)

		if window.name is None:
			name_conflicts = sorted(self._namespace.keys() & window._namespace.keys())
			if name_conflicts:
				name_conflict_descrs = [
					f'{name} is used by {self._namespace[name]!r}' for name in name_conflicts
				]
				raise ValueError(f'The following names are already used: {"; ".join(name_conflict_descrs)}')
		else:
			if window.name in self._namespace:
				raise ValueError(f'Name {window.name} is already used by {self._namespace[window.name]!r}')

		if not sparse:
			ratio = self.data_width // window.data_width
		else:
			ratio = 1
		size = (1 << window.addr_width) // ratio
		# For resources, the alignment argument of add_resource() affects both address and size
		# of the resource; aligning only the address should be done using align_to(). For windows,
		# changing the size (beyond the edge case of the window size being smaller than alignment
		# of the bus) is unlikely to be useful, so there is no alignment argument. The address of
		# a window can still be aligned using align_to().
		alignment = max(self.alignment, window.addr_width // ratio)

		addr_range = self._compute_addr_range(
			addr, size, ratio, alignment = alignment, extend = extend
		)
		window.freeze()
		self._ranges.insert(addr_range, window)
		self._windows[id(window)] = window, addr_range
		if window.name is None:
			self._namespace.update(window._namespace)
		else:
			self._namespace[window.name] = window
		self._next_addr = addr_range.stop
		return addr_range.start, addr_range.stop, addr_range.step

	def windows(self):
		'''Iterate local windows and their address ranges.

		Non-recursively iterate windows in ascending order of their address.

		Yield values
		------------
		A tuple ``window, (start, end, ratio)`` describing the address range assigned to
		the window. When bridging buses of unequal data width, ``ratio`` is the amount of
		contiguous addresses on the narrower bus that are accessed for each transaction on
		the wider bus. Otherwise, it is always 1.
		'''
		for window, window_range in self._windows.values():
			yield (window, (window_range.start, window_range.stop, window_range.step))

	def window_patterns(self) -> Generator[Tuple[object, Tuple[str, int]], None, None]:
		'''Iterate local windows and patterns that match their address ranges.

		Non-recursively iterate windows in ascending order of their address.

		Yield values
		------------
		A tuple ``window, (pattern, ratio)`` describing the address range assigned to the window.
		``pattern`` is a ``self.addr_width`` wide pattern that may be used in ``Case`` or ``match``
		to determine if an address signal is within the address range of ``window``. When bridging
		buses of unequal data width, ``ratio`` is the amount of contiguous addresses on
		the narrower bus that are accessed for each transaction on the wider bus. Otherwise,
		it is always 1.
		'''
		for window, window_range in self._windows.values():
			const_bits = self.addr_width - window.addr_width
			if const_bits > 0:
				const_pat = f'{window_range.start >> window.addr_width:0{const_bits}b}'
			else:
				const_pat = ''
			pattern = f'{const_pat}{"-" * window.addr_width}'
			yield (window, (pattern, window_range.step))

	@staticmethod
	def _translate(
		resource_info : ResourceInfo, window, window_range : range
	) -> ResourceInfo:
		assert (resource_info.end - resource_info.start) % window_range.step == 0
		# Accessing a resource through a dense and then a sparse window results in very strange
		# layouts that cannot be easily represented, so reject those.
		assert window_range.step == 1 or resource_info.width == window.data_width

		name  = resource_info.name if window.name is None else (window.name, *resource_info.name)
		size  = (resource_info.end - resource_info.start) // window_range.step
		start = resource_info.start + window_range.start
		width = resource_info.width * window_range.step
		return ResourceInfo(resource_info.resource, name, start, start + size, width)

	def all_resources(self) -> Generator[ResourceInfo, None, None]:
		'''Iterate all resources and their address ranges.

		Recursively iterate all resources in ascending order of their address, performing address
		translation for resources that are located behind a window.

		Yield values
		------------
		An instance of :class:`ResourceInfo` describing the resource and its address range.
		'''
		for addr_range, assignment in self._ranges.items():
			if id(assignment) in self._resources:
				_, resource_name, _ = self._resources[id(assignment)]
				yield ResourceInfo(
					assignment, resource_name, addr_range.start, addr_range.stop, self.data_width
				)
			elif id(assignment) in self._windows:
				for resource_info in assignment.all_resources():
					yield self._translate(resource_info, assignment, addr_range)
			else:
				assert False # :nocov:

	def find_resource(self, resource : object) -> ResourceInfo:
		'''Find address range corresponding to a resource.

		Recursively find the address range of a resource, performing address translation for
		resources that are located behind a window.

		Arguments
		---------
		resource
			Resource previously added to this memory map or any windows.

		Return value
		------------
		An instance of :class:`ResourceInfo` describing the resource and its address range.

		Exceptions
		----------
		Raises :exn:`KeyError` if the resource is not found.
		'''
		if id(resource) in self._resources:
			_, resource_name, resource_range = self._resources[id(resource)]
			return ResourceInfo(resource, resource_name, resource_range.start, resource_range.stop,
								self.data_width)

		for window, window_range in self._windows.values():
			try:
				return self._translate(window.find_resource(resource), window, window_range)
			except KeyError:
				pass

		raise KeyError(resource)

	def decode_address(self, address : int) -> Optional[object]:
		'''Decode an address to a resource.

		Arguments
		---------
		address : int
			Address of interest.

		Return value
		------------
		A resource mapped to the provided address, or ``None`` if there is no such resource.
		'''
		assignment = self._ranges.get(address)
		if assignment is None:
			return

		if id(assignment) in self._resources:
			return assignment
		elif id(assignment) in self._windows:
			_, addr_range = self._windows[id(assignment)]
			return assignment.decode_address((address - addr_range.start) // addr_range.step)
		else:
			assert False # :nocov:
