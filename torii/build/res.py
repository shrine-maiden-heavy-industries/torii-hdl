# SPDX-License-Identifier: BSD-2-Clause

from collections import OrderedDict
from typing      import (
	List, Optional, Literal, Dict, Union,
	Generator, Tuple
)

from ..hdl.ast   import *
from ..hdl.rec   import *
from ..lib.io    import *
from .dsl        import *

__all__ = (
	'ResourceError',
	'ResourceManager',
)


class ResourceError(Exception):
	pass


class ResourceManager:
	def __init__(self, resources : List[Resource], connectors : List[Connector]) -> None:
		self.resources  = OrderedDict()
		self._requested = OrderedDict()
		self._phys_reqd = OrderedDict()

		self.connectors = OrderedDict()
		self._conn_pins = OrderedDict()

		# Constraint lists
		self._ports     = []
		self._clocks    = SignalDict()

		self.add_resources(resources)
		self.add_connectors(connectors)

	def add_resources(self, resources : List[Resource]) -> None:
		for res in resources:
			if not isinstance(res, Resource):
				raise TypeError(f'Object {res!r} is not a Resource')
			if (res.name, res.number) in self.resources:
				raise NameError(f'Trying to add {res!r}, but {self.resources[res.name, res.number]!r} has the same name and number')

			self.resources[res.name, res.number] = res

	def add_connectors(self, connectors : List[Connector]) -> None:
		for conn in connectors:
			if not isinstance(conn, Connector):
				raise TypeError(f'Object {conn!r} is not a Connector')
			if (conn.name, conn.number) in self.connectors:
				raise NameError(f'Trying to add {conn!r}, but {self.connectors[conn.name, conn.number]!r} has the same name and number')

			self.connectors[conn.name, conn.number] = conn

			for conn_pin, plat_pin in conn:
				assert conn_pin not in self._conn_pins
				self._conn_pins[conn_pin] = plat_pin

	def lookup(self, name : str , number : int = 0) -> Resource:
		if (name, number) not in self.resources:
			raise ResourceError(f'Resource {name}#{number} does not exist')

		return self.resources[name, number]

	def request(
		self, name : str, number : int = 0, *,
		dir : Optional[Literal['i', 'o', 'oe', 'io', '-']] = None,
		xdr : Optional[Dict[str, int]] = None
	) -> Union[Record, Pin]:
		resource = self.lookup(name, number)
		if (resource.name, resource.number) in self._requested:
			raise ResourceError(f'Resource {name}#{number} has already been requested')

		def merge_options(
			subsignal : Subsignal,
			dir : Optional[Union[Literal['i', 'o', 'oe', 'io', '-'], Dict[str, Literal['i', 'o', 'oe', 'io', '-']]]],
			xdr : Optional[Union[int, Dict[str, int]]]
		) -> Tuple[
			Union[
				Literal['i', 'o', 'oe', 'io', '-'],
				Dict[str, Literal['i', 'o', 'oe', 'io', '-']]
			],
			Union[int, Dict[str, int]]
		]:
			if isinstance(subsignal.ios[0], Subsignal):
				if dir is None:
					dir = dict()
				if xdr is None:
					xdr = dict()
				if not isinstance(dir, dict):
					raise TypeError(f'Directions must be a dict, not {dir!r}, because {subsignal!r} has subsignals')

				if not isinstance(xdr, dict):
					raise TypeError(f'Data rate must be a dict, not {xdr!r}, because {subsignal!r} has subsignals')

				for sub in subsignal.ios:
					sub_dir = dir.get(sub.name, None)
					sub_xdr = xdr.get(sub.name, None)
					dir[sub.name], xdr[sub.name] = merge_options(sub, sub_dir, sub_xdr)
			else:
				if dir is None:
					dir = subsignal.ios[0].dir
				if xdr is None:
					xdr = 0
				if dir not in ('i', 'o', 'oe', 'io', '-'):
					raise TypeError(
						f'Direction must be one of \'i\', \'o\', \'oe\', \'io\', or \'-\', not {dir!r}'
					)
				if dir != subsignal.ios[0].dir and not (subsignal.ios[0].dir == 'io' or dir == '-'):
					raise ValueError(
						f'Direction of {subsignal.ios[0]!r} cannot be changed from \'{subsignal.ios[0].dir}\' '
						f'to \'{dir}\'; direction can be changed from \'io\' to \'i\', \'o\', or '
						'\'oe\', or from anything to \'-\''
					)

				if not isinstance(xdr, int) or xdr < 0:
					raise ValueError(f'Data rate of {subsignal.ios[0]!r} must be a non-negative integer, not {xdr!r}')

			return (dir, xdr)

		def resolve(
			resource : Resource,
			dir : Union[Literal['i', 'o', 'oe', 'io', '-'], Dict[str, Literal['i', 'o', 'oe', 'io', '-']]],
			xdr : Union[int, Dict[str, int]],
			name : str, attrs : Attrs
		) -> Union[Record, Pin]:
			for attr_key, attr_value in attrs.items():
				if hasattr(attr_value, '__call__'):
					attr_value = attr_value(self)
					assert attr_value is None or isinstance(attr_value, str)
				if attr_value is None:
					del attrs[attr_key]
				else:
					attrs[attr_key] = attr_value

			if isinstance(resource.ios[0], Subsignal):
				fields = OrderedDict()
				for sub in resource.ios:
					fields[sub.name] = resolve(
						sub, dir[sub.name], xdr[sub.name],
						name = f'{name}__{sub.name}',
						attrs = {**attrs, **sub.attrs}
					)
				return Record([
					(f_name, f.layout) for (f_name, f) in fields.items()
				], fields = fields, name = name)

			elif isinstance(resource.ios[0], (Pins, DiffPairs)):
				phys = resource.ios[0]
				if isinstance(phys, Pins):
					phys_names = phys.names
					port = Record([('io', len(phys))], name = name)
				if isinstance(phys, DiffPairs):
					phys_names = []
					record_fields = []
					if not self.should_skip_port_component(None, attrs, 'p'):
						phys_names += phys.p.names
						record_fields.append(('p', len(phys)))
					if not self.should_skip_port_component(None, attrs, 'n'):
						phys_names += phys.n.names
						record_fields.append(('n', len(phys)))
					port = Record(record_fields, name = name)
				if dir == '-':
					pin = None
				else:
					pin = Pin(len(phys), dir, xdr=xdr, name=name)

				for phys_name in phys_names:
					if phys_name in self._phys_reqd:
						raise ResourceError(
							f'Resource component {name} uses physical pin {phys_name}, but it '
							f'is already used by resource component {self._phys_reqd[phys_name]} that was '
							'requested earlier'
						)

					self._phys_reqd[phys_name] = name

				self._ports.append((resource, pin, port, attrs))

				if pin is not None and resource.clock is not None:
					self.add_clock_constraint(pin.i, resource.clock.frequency)

				return pin if pin is not None else port

			else:
				assert False # :nocov:

		value = resolve(
			resource,
			*merge_options(resource, dir, xdr),
			name = f'{resource.name}_{resource.number}',
			attrs = resource.attrs
		)
		self._requested[resource.name, resource.number] = value
		return value

	def iter_single_ended_pins(self) -> Generator[Tuple[
		Pin, Subsignal, Attrs, bool
	], None, None]:
		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], Pins):
				yield (pin, port, attrs, res.ios[0].invert)

	def iter_differential_pins(self) -> Generator[Tuple[
		Pin, Subsignal, Attrs, bool
	], None, None]:
		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], DiffPairs):
				yield (pin, port, attrs, res.ios[0].invert)

	def should_skip_port_component(
		self, port : Subsignal, attrs : Attrs, component : Literal['io', 'i', 'o', 'p', 'n', 'oe']
	) -> bool:
		return False

	def iter_ports(self) -> Generator[Signal, None, None]:
		for res, pin, port, attrs in self._ports:
			if isinstance(res.ios[0], Pins):
				if not self.should_skip_port_component(port, attrs, 'io'):
					yield port.io
			elif isinstance(res.ios[0], DiffPairs):
				if not self.should_skip_port_component(port, attrs, 'p'):
					yield port.p
				if not self.should_skip_port_component(port, attrs, 'n'):
					yield port.n
			else:
				assert False

	def iter_port_constraints(self) -> Generator[
		Tuple[str, str, Attrs], None, None
	]:
		for res, pin, port, attrs in self._ports:
			if isinstance(res.ios[0], Pins):
				if not self.should_skip_port_component(port, attrs, 'io'):
					yield (port.io.name, res.ios[0].map_names(self._conn_pins, res), attrs)
			elif isinstance(res.ios[0], DiffPairs):
				if not self.should_skip_port_component(port, attrs, 'p'):
					yield (port.p.name, res.ios[0].p.map_names(self._conn_pins, res), attrs)
				if not self.should_skip_port_component(port, attrs, 'n'):
					yield (port.n.name, res.ios[0].n.map_names(self._conn_pins, res), attrs)
			else:
				assert False

	def iter_port_constraints_bits(self) -> Generator[
		Tuple[str, str, Attrs], None, None
	]:
		for port_name, pin_names, attrs in self.iter_port_constraints():
			if len(pin_names) == 1:
				yield (port_name, pin_names[0], attrs)
			else:
				for bit, pin_name in enumerate(pin_names):
					yield (f'{port_name}[{bit}]', pin_name, attrs)

	def add_clock_constraint(self, clock : Signal, frequency : Union[int, float]) -> None:
		if not isinstance(clock, Signal):
			raise TypeError(f'Object {clock!r} is not a Signal')
		if not isinstance(frequency, (int, float)):
			raise TypeError(f'Frequency must be a number, not {frequency!r}')

		if clock in self._clocks:
			raise ValueError(f'Cannot add clock constraint on {clock!r}, which is already constrained to {self._clocks[clock]} Hz')

		else:
			self._clocks[clock] = float(frequency)

	def iter_clock_constraints(self) -> Generator[
		Tuple[str, Signal, float], None, None
	]:
		# Back-propagate constraints through the input buffer. For clock constraints on pins
		# (the majority of cases), toolchains work better if the constraint is defined on the pin
		# and not on the buffered internal net; and if the toolchain is advanced enough that
		# it considers clock phase and delay of the input buffer, it is *necessary* to define
		# the constraint on the pin to match the designer's expectation of phase being referenced
		# to the pin.
		#
		# Constraints on nets with no corresponding input pin (e.g. PLL or SERDES outputs) are not
		# affected.
		pin_i_to_port = SignalDict()
		for res, pin, port, attrs in self._ports:
			if hasattr(pin, 'i'):
				if isinstance(res.ios[0], Pins):
					pin_i_to_port[pin.i] = port.io
				elif isinstance(res.ios[0], DiffPairs):
					pin_i_to_port[pin.i] = port.p
				else:
					raise ValueError(f'Expected res.ios[0] to be a \'Pins\' or \'DiffPairs\', not {res.ios[0]!r}')

		for net_signal, frequency in self._clocks.items():
			port_signal = pin_i_to_port.get(net_signal)
			yield (net_signal, port_signal, frequency)
