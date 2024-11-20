# SPDX-License-Identifier: BSD-2-Clause

from collections     import OrderedDict
from collections.abc import Generator, Iterable, Callable
from typing          import Literal


from .._typing       import IODirectionEmpty
from ..hdl.ast       import Signal, SignalDict, Value, ValueCastable
from ..hdl.rec       import Record
from ..lib.io        import Pin
from .dsl            import Attrs, Connector, DiffPairs, Pins, Resource, Subsignal

__all__ = (
	'ResourceError',
	'ResourceManager',
)


class ResourceError(Exception):
	pass


class ResourceManager:
	def __init__(self, resources: list[Resource], connectors: list[Connector]) -> None:
		self.resources  = OrderedDict[tuple[str, int], Resource]()
		self._requested = OrderedDict[tuple[str, int], Record | Pin]()
		self._phys_reqd = OrderedDict[str, str]()

		self.connectors = OrderedDict[tuple[str, int], Connector]()
		self._conn_pins = OrderedDict[str, str]()

		# Constraint lists
		self._ports     = list[tuple[Resource, Pin | None, Record, Attrs]]()
		self._clocks    = SignalDict[float]()

		self.add_resources(resources)
		self.add_connectors(connectors)

	def add_resources(self, resources: Iterable[Resource]) -> None:
		for res in resources:
			if not isinstance(res, Resource):
				raise TypeError(f'Object {res!r} is not a Resource')
			if (res.name, res.number) in self.resources:
				raise NameError(f'Trying to add {res!r}, but {self.resources[res.name, res.number]!r} has the same name and number')

			self.resources[res.name, res.number] = res

	def add_connectors(self, connectors: Iterable[Connector]) -> None:
		for conn in connectors:
			if not isinstance(conn, Connector):
				raise TypeError(f'Object {conn!r} is not a Connector')
			if (conn.name, conn.number) in self.connectors:
				raise NameError(
					f'Trying to add {conn!r}, but {self.connectors[conn.name, conn.number]!r} '
					'has the same name and number'
				)

			self.connectors[conn.name, conn.number] = conn

			for conn_pin, plat_pin in conn:
				if conn_pin in self._conn_pins:
					raise ValueError(f'Connector pin {conn_pin!r} already in connector!')
				self._conn_pins[conn_pin] = plat_pin

	def lookup(self, name: str , number: int = 0) -> Resource:
		if (name, number) not in self.resources:
			raise ResourceError(f'Resource {name}#{number} does not exist')

		return self.resources[name, number]

	def request(
		self, name: str, number: int = 0, *,
		dir: IODirectionEmpty | None = None,
		xdr: dict[str, int] | None = None
	) -> Record | Pin:
		resource = self.lookup(name, number)
		if (resource.name, resource.number) in self._requested:
			raise ResourceError(f'Resource {name}#{number} has already been requested')

		def merge_options(
			subsignal: Subsignal,
			dir: IODirectionEmpty | dict[str, IODirectionEmpty] | None,
			xdr: int | dict[str, int] | None
		) -> tuple[IODirectionEmpty, int] | tuple[dict[str, IODirectionEmpty], dict[str, int]]:

			if isinstance(subsignal.ios[0], Subsignal):
				if dir is None:
					dir = dict[str, IODirectionEmpty]()
				if xdr is None:
					xdr = dict[str, int]()

				if not isinstance(dir, dict):
					raise TypeError(f'Directions must be a dict, not {dir!r}, because {subsignal!r} has subsignals')

				if not isinstance(xdr, dict):
					raise TypeError(f'Data rate must be a dict, not {xdr!r}, because {subsignal!r} has subsignals')

				for sub in subsignal.ios:
					assert isinstance(sub, Subsignal)

					sub_dir = dir.get(sub.name, None)
					sub_xdr = xdr.get(sub.name, None)
					dir[sub.name], xdr[sub.name] = merge_options(sub, sub_dir, sub_xdr)
			else:
				pin = subsignal.ios[0]
				assert isinstance(pin, (Pins, DiffPairs))

				if dir is None:
					dir: str = pin.dir

				if xdr is None:
					xdr = 0

				if dir not in ('i', 'o', 'oe', 'io', '-'):
					raise TypeError(
						f'Direction must be one of \'i\', \'o\', \'oe\', \'io\', or \'-\', not {dir!r}'
					)
				if dir != pin.dir and not (pin.dir == 'io' or dir == '-'):
					raise ValueError(
						f'Direction of {pin!r} cannot be changed from \'{pin.dir}\' '
						f'to \'{dir}\'; direction can be changed from \'io\' to \'i\', \'o\', or '
						'\'oe\', or from anything to \'-\''
					)

				if not isinstance(xdr, int) or xdr < 0:
					raise ValueError(f'Data rate of {subsignal.ios[0]!r} must be a non-negative integer, not {xdr!r}')

			return (dir, xdr)

		def resolve(
			resource: Resource | Subsignal,
			dir: IODirectionEmpty | dict[str, IODirectionEmpty],
			xdr: int | dict[str, int],
			name: str, attrs: Attrs
		) -> Record | Pin:
			for attr_key, attr_value in attrs.items():
				if isinstance(attr_value, Callable):
					attr_value = attr_value(self)
					if attr_value is not None or not isinstance(attr_value, str):
						raise TypeError(f'attr_value is expected to be either a str or None, not \'{attr_value!r}\'')

				if attr_value is None:
					del attrs[attr_key]
				else:
					attrs[attr_key] = attr_value

			if isinstance(resource.ios[0], Subsignal):
				fields = OrderedDict[str, Record | Pin]()
				assert isinstance(dir, dict)
				assert isinstance(xdr, dict)
				for sub in resource.ios:
					assert isinstance(sub, Subsignal)
					fields[sub.name] = resolve(
						sub, dir[sub.name], xdr[sub.name],
						name = f'{name}__{sub.name}',
						attrs = Attrs(**attrs, **sub.attrs)
					)
				return Record([
					(f_name, f.layout) for (f_name, f) in fields.items()
				], fields = fields, name = name)

			elif isinstance(resource.ios[0], (Pins, DiffPairs)):
				assert isinstance(xdr, int)
				assert isinstance(dir, str)

				phys = resource.ios[0]
				if isinstance(phys, Pins):
					phys_names = phys.names
					port = Record([('io', len(phys))], name = name)
				elif isinstance(phys, DiffPairs):
					phys_names = []
					record_fields = []
					if not self.should_skip_port_component(None, attrs, 'p'):
						phys_names += phys.p.names
						record_fields.append(('p', len(phys)))
					if not self.should_skip_port_component(None, attrs, 'n'):
						phys_names += phys.n.names
						record_fields.append(('n', len(phys)))
					port = Record(record_fields, name = name)
				else:
					raise TypeError(f'How did you even get here? type: {phys!r}')

				if dir == '-':
					pin = None
				else:
					pin = Pin(len(phys), dir, xdr = xdr, name = name)

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
				raise TypeError(f'Expected a Subsignal, Pin, or DiffPairs, not a \'{resource.ios[0]!r}\'') # :nocov:

		value = resolve(
			resource,
			*merge_options(resource, dir, xdr),
			name = f'{resource.name}_{resource.number}',
			attrs = resource.attrs
		)
		self._requested[resource.name, resource.number] = value
		return value

	def iter_single_ended_pins(self) -> Generator[tuple[
		Pin, Record, Attrs, bool
	], None, None]:
		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], Pins):
				yield (pin, port, attrs, res.ios[0].invert)

	def iter_differential_pins(self) -> Generator[tuple[
		Pin, Record, Attrs, bool
	], None, None]:
		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], DiffPairs):
				yield (pin, port, attrs, res.ios[0].invert)

	def should_skip_port_component(
		self, port: Record | None, attrs: Attrs, component: Literal['io', 'i', 'o', 'p', 'n', 'oe']
	) -> bool:
		return False

	def iter_ports(self) -> Generator[ValueCastable | Value, None, None]:
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
				raise TypeError(f'Expected either \'Pins\', or \'DiffPairs\', not \'{res.ios[0]!r}\'')

	def iter_port_constraints(self):
		for res, pin, port, attrs in self._ports:
			if isinstance(res.ios[0], Pins):
				assert isinstance(port.io, Signal)
				if not self.should_skip_port_component(port, attrs, 'io'):
					yield (port.io.name, res.ios[0].map_names(self._conn_pins, res), attrs)
			elif isinstance(res.ios[0], DiffPairs):
				if not self.should_skip_port_component(port, attrs, 'p'):
					assert isinstance(port.p, Signal)
					yield (port.p.name, res.ios[0].p.map_names(self._conn_pins, res), attrs)
				if not self.should_skip_port_component(port, attrs, 'n'):
					assert isinstance(port.n, Signal)
					yield (port.n.name, res.ios[0].n.map_names(self._conn_pins, res), attrs)
			else:
				raise TypeError(f'Expected either \'Pins\', or \'DiffPairs\', not \'{res.ios[0]!r}\'')

	def iter_port_constraints_bits(self) -> Generator[
		tuple[str, str, Attrs], None, None
	]:
		for port_name, pin_names, attrs in self.iter_port_constraints():
			if len(pin_names) == 1:
				yield (port_name, pin_names[0], attrs)
			else:
				for bit, pin_name in enumerate(pin_names):
					yield (f'{port_name}[{bit}]', pin_name, attrs)

	def add_clock_constraint(self, clock: Signal, frequency: int | float) -> None:
		if not isinstance(clock, Signal):
			raise TypeError(f'Object {clock!r} is not a Signal')
		if not isinstance(frequency, (int, float)):
			raise TypeError(f'Frequency must be a number, not {frequency!r}')

		if clock in self._clocks:
			raise ValueError(
				f'Cannot add clock constraint on {clock!r}, which is already constrained to {self._clocks[clock]} Hz'
			)

		else:
			self._clocks[clock] = float(frequency)

	def iter_clock_constraints(self) -> Generator[
		tuple[Signal | None, Signal | None, float], None, None
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
		pin_i_to_port = SignalDict[Signal]()
		for res, pin, port, attrs in self._ports:
			if hasattr(pin, 'i'):
				assert pin is not None
				if isinstance(res.ios[0], Pins):
					pin_i_to_port[pin.i] = port.io
				elif isinstance(res.ios[0], DiffPairs):
					pin_i_to_port[pin.i] = port.p
				else:
					raise ValueError(f'Expected res.ios[0] to be a \'Pins\' or \'DiffPairs\', not {res.ios[0]!r}')

		for net_signal, frequency in self._clocks.items():
			port_signal = pin_i_to_port.get(net_signal)
			yield (net_signal, port_signal, frequency)
