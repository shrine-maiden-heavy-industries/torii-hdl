# SPDX-License-Identifier: BSD-2-Clause

from collections     import OrderedDict
from collections.abc import Callable, Generator, Iterable
from typing          import Literal
from warnings        import warn

from ..diagnostics   import ConstraintError, ResourceError, ToriiSyntaxError
from .._typing       import IODirectionEmpty, SrcLoc
from ..hdl.ast       import Signal, SignalDict, Value, ValueCastable
from ..hdl.rec       import Record
from ..hdl.time      import Frequency
from ..lib.io        import Pin
from ..util.string   import _get_best_matching
from ..util.tracer   import get_src_loc
from .dsl            import Attrs, Connector, DiffPairs, Pins, Resource, Subsignal

__all__ = (
	'ResourceManager',
)

class ResourceManager:
	'''
	The base resource manager for Torii platforms.

	It is responsible for keeping track of and doing resource and connector resolution,
	as well as generating constraints for I/O and clocking where appropriate.

	Parameters
	----------
	resources: list[Resource]
		The list of resources to manage

	connectors: list[Connectors]
		The list of connectors to manage
	'''

	def __init__(self, resources: list[Resource], connectors: list[Connector]) -> None:
		self.resources  = OrderedDict[tuple[str, int], Resource]()
		self._requested = OrderedDict[tuple[str, int], tuple[Record | Pin, SrcLoc]]()
		self._phys_reqd = OrderedDict[str, tuple[str, SrcLoc]]()

		self.connectors = OrderedDict[tuple[str, int], Connector]()
		self._conn_pins = OrderedDict[str, str]()

		# Constraint lists
		self._ports     = list[tuple[Resource, Pin | None, Record, Attrs]]()
		self._clocks    = SignalDict[tuple[Frequency, SrcLoc]]()

		self.add_resources(resources)
		self.add_connectors(connectors)

	def add_resources(self, resources: Iterable[Resource], *, src_loc_at: int = 0) -> None:
		'''
		Add one or more :py:class:`Resource <torii.build.dsl.Resource>`'s to the current platform.

		Parameters
		----------
		resources: Iterable[Resource]
			The Torii resources to add

		Raises
		------
		ToriiSyntaxError
			If an element in the resource list is not a :py:class:`Resource <torii.build.dsl.Resource>`

		ResourceError
			If the resource already exists
		'''

		for res in resources:
			if not isinstance(res, Resource):
				raise ToriiSyntaxError(
					f'Object {res!r} is not a Resource', src_loc = get_src_loc(src_loc_at)
				)
			if (res.name, res.number) in self.resources:
				ext_res = self.resources[res.name, res.number]

				notes = list[str]()

				if repr(res) == repr(ext_res):
					notes.append(
						'The previously defined resource appears to be identical to the current one'
					)
				else:
					notes.append(
						f'The previously defined resource has {len(ext_res.ios)} subsignals while the current resource '
						f'has {len(res.ios)}',
					)

				raise ResourceError(
					message = (
						f'Trying to add the resource {res.name}#{res.number}, but there is a previously added '
						'resource that has the same name and number'
					),
					src_loc = res.src_loc,
					notes = notes,
					additional_ctx = (
						'Previous resource was declared here:',
						ext_res.src_loc
					)
				)

			self.resources[res.name, res.number] = res

	def add_connectors(self, connectors: Iterable[Connector], *, src_loc_at: int = 0) -> None:
		'''
		Add one or more :py:class:`Connector <torii.build.dsl.Connector>`'s to the current platform.

		Parameters
		----------
		connectors: Iterable[Connector]
			The Torii connectors to add

		Raises
		------
		ToriiSyntaxError
			If an element in the connectors list is not a :py:class:`Connector <torii.build.dsl.Connector>`

		ResourceError
			If the connector already exists

		ResourceError
			If a pin in the given connector is used by another connector
		'''

		for conn in connectors:
			if not isinstance(conn, Connector):
				raise ToriiSyntaxError(
					f'Object {conn!r} is not a Connector', src_loc = get_src_loc(src_loc_at)
				)
			if (conn.name, conn.number) in self.connectors:
				ext_conn = self.connectors[conn.name, conn.number]

				notes = list[str]()

				if conn.__repr__() == ext_conn.__repr__():
					notes.append(
						'The previously defined connector appears to be identical to the current one'
					)
				else:
					notes.append(
						f'The previously defined connector has {len(ext_conn.mapping.keys())} connections while the '
						f'current connector has {len(conn.mapping.keys())}',
					)

				raise ResourceError(
					message = (
						f'Trying to add the connector {conn.name}#{conn.number}, but there is a previously added '
						'connector that has the same name and number'
					),
					src_loc = conn.src_loc,
					notes = notes,
					additional_ctx = (
						'Previous connector was declared here:',
						ext_conn.src_loc
					)
				)

			self.connectors[conn.name, conn.number] = conn

			for conn_pin, plat_pin in conn:
				if conn_pin in self._conn_pins:
					raise ResourceError(
						message = f'Connector pin {conn_pin!r} already in connector!',
						src_loc = conn.src_loc
					)
				self._conn_pins[conn_pin] = plat_pin

	def lookup(self, name: str, number: int = 0, *, src_loc_at: int = 0) -> Resource:
		'''
		Attempt to get the resource with the given name an number

		Parameters
		----------
		name: str
			The name of the resource to look for

		number: int
			The number of the resource to look for

		Returns
		-------
		Resource
			The resource if found

		Raises
		------
		ResourceError
			If the resource is not found
		'''

		if (name, number) not in self.resources:
			src_loc = get_src_loc(src_loc_at)
			matches = _get_best_matching(f'{name}#{number}', map(lambda r: f'{r[0]}#{r[1]}', self.resources.keys()))
			additional_ctx = None

			if len(matches) > 0:
				match = matches[0]
				message = f'The resource {name}#{number} was requested but does not exist, did you mean {match}?'
				mname, mnumber = match.split('#')
				additional_ctx = (
					f'The resource {match} was defined here:',
					self.resources[(mname, int(mnumber))].src_loc
				)
			else:
				message = f'The resource {name}#{number} was requested, but does not exist'

			raise ResourceError(
				message = message, src_loc = src_loc, additional_ctx = additional_ctx
			)

		return self.resources[name, number]

	def request(
		self, name: str, number: int = 0, *,
		dir: IODirectionEmpty | None = None,
		xdr: dict[str, int] | None = None
	) -> Record | Pin:
		'''
		Request the given resource from the platform.

		Parameters
		----------
		name: str
			The name of the resource to request

		number: int
			The number of the resource to request

		dir: IODirection | None
			The IO direction for the resource

		xdr: dict[str, int] | None
			The IO gearing for the resource
		'''

		src_loc = get_src_loc()

		resource = self.lookup(name, number, src_loc_at = 1)
		if (resource.name, resource.number) in self._requested:
			raise ResourceError(
				message = f'The resource {name}#{number} has previously been requested',
				src_loc = src_loc,
				notes = [
					'In order to prevent conflicts, Torii resources can only be requested once'
				],
				additional_ctx = (
					f'The resource {name}#{number} was previously requested here:',
					self._requested[(resource.name, resource.number)][1]
				)
			)

		def merge_options(
			subsignal: Subsignal,
			dir: IODirectionEmpty | dict[str, IODirectionEmpty] | None,
			xdr: int | dict[str, int] | None
		) -> tuple[IODirectionEmpty, int] | tuple[dict[str, IODirectionEmpty], dict[str, int]]:
			'''
			.. todo:: Document Me
			'''

			if isinstance(subsignal.ios[0], Subsignal):
				if dir is None:
					dir = dict[str, IODirectionEmpty]()
				if xdr is None:
					xdr = dict[str, int]()

				if not isinstance(dir, dict):
					subsigs = list(map(lambda s: f'\'{s.name}\'', subsignal.ios))
					raise ResourceError(
						message = (
							f'Directions must be a dict, not {dir!r}, because {subsignal.name} has '
							f'{len(subsigs)} subsignals'
						),
						src_loc = src_loc,
						notes = [
							f'The following subsignals are present in {subsignal.name}: {", ".join(subsigs)}',
							f'For example, to set the direction for {subsigs[0]}, use {{{subsigs[0]}: \'-\' }}'
						]
					)

				if not isinstance(xdr, dict):
					subsigs = list(map(lambda s: f'\'{s.name}\'', subsignal.ios))
					raise ResourceError(
						message = (
							f'Data rate must be a dict, not {xdr!r}, because {subsignal.name} has '
							f'{len(subsigs)} subsignals'
						),
						src_loc = src_loc,
						notes = [
							f'The following subsignals are present in {subsignal.name}: {", ".join(subsigs)}',
							f'For example, to set the gearing for {subsigs[0]}, use {{{subsigs[0]}: {xdr} }}'
						]
					)

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
					raise ToriiSyntaxError(
						f'Direction must be one of \'i\', \'o\', \'oe\', \'io\', or \'-\', not {dir!r}',
						src_loc = pin.src_loc
					)
				if dir != pin.dir and not (pin.dir == 'io' or dir == '-'):
					raise ToriiSyntaxError(
						f'Direction of {pin!r} cannot be changed from \'{pin.dir}\' '
						f'to \'{dir}\'; direction can be changed from \'io\' to \'i\', \'o\', or '
						'\'oe\', or from anything to \'-\'',
						src_loc = pin.src_loc
					)

				if not isinstance(xdr, int) or xdr < 0:
					raise ToriiSyntaxError(
						f'Data rate of {subsignal.ios[0]!r} must be a non-negative integer, not {xdr!r}',
						src_loc = subsignal.src_loc
					)

			return (dir, xdr)

		def resolve(
			resource: Resource | Subsignal,
			dir: IODirectionEmpty | dict[str, IODirectionEmpty],
			xdr: int | dict[str, int],
			name: str, attrs: Attrs
		) -> Record | Pin:
			'''
			.. todo:: Document Me
			'''

			for attr_key, attr_value in attrs.items():
				if isinstance(attr_value, Callable):
					attr_value = attr_value(self)
					if attr_value is not None or not isinstance(attr_value, str):
						raise ToriiSyntaxError(
							f'attr_value is expected to be either a str or None, not \'{attr_value!r}\'',
							src_loc = attrs.src_loc
						)

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
					pin = Pin(len(phys), dir, xdr = xdr, name = name, diff = isinstance(phys, DiffPairs))
					# Adjust source location, as this pin is dynamically generated at the request location
					pin.src_loc = src_loc

				for phys_name in phys_names:
					if phys_name in self._phys_reqd:
						pname, ploc = self._phys_reqd[phys_name]

						raise ResourceError(
							message = (
								f'Resource component {name} uses physical pin {phys_name}, but it '
								f'is already used by resource component {pname} that was '
								'requested earlier'
							),
							src_loc = src_loc,
							additional_ctx = (
								f'Pin {phys_name} was previously requested here:',
								ploc
							)
						)

					self._phys_reqd[phys_name] = (name, src_loc)

				self._ports.append((resource, pin, port, attrs))

				if pin is not None and resource.clock is not None:
					self.add_clock_constraint(pin.i, resource.clock.frequency)
					# Fix-up the source location information
					self._clocks[pin.i] = (self._clocks[pin.i][0], resource.clock.src_loc)

				return pin if pin is not None else port

			else:
				raise ToriiSyntaxError(
					f'Expected a Subsignal, Pin, or DiffPairs, not a \'{resource.ios[0]!r}\'',
					src_loc = resource.src_loc
				) # :nocov:

		value = resolve(
			resource,
			*merge_options(resource, dir, xdr),
			name = f'{resource.name}_{resource.number}',
			attrs = resource.attrs
		)
		self._requested[resource.name, resource.number] = (value, src_loc)
		return value

	def iter_single_ended_pins(self) -> Generator[tuple[
		Pin, Record, Attrs, bool, Iterable[str]
	], None, None]:
		''' Iterate over all single-ended pins in all resources '''

		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], Pins):
				yield (pin, port, attrs, res.ios[0].invert, res.ios[0].map_names(self._conn_pins, res))

	def iter_differential_pins(self) -> Generator[tuple[
		Pin, Record, Attrs, bool, tuple[Iterable[str], Iterable[str]]
	], None, None]:
		''' Iterate over all differential pins in all resources '''

		for res, pin, port, attrs in self._ports:
			if pin is None:
				continue
			if isinstance(res.ios[0], DiffPairs):
				yield (
					pin, port, attrs, res.ios[0].invert,
					(res.ios[0].p.map_names(self._conn_pins, res), res.ios[0].n.map_names(self._conn_pins, res))
				)

	def should_skip_port_component(
		self, port: Record | None, attrs: Attrs, component: Literal['io', 'i', 'o', 'p', 'n', 'oe']
	) -> bool:
		''' Determine if the given port should be skipped or not '''

		return False

	def iter_ports(self) -> Generator[ValueCastable | Value, None, None]:
		''' Iterate over all ports in all resources '''

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
		''' Iterate over all ports in all resources for the purpose of generating IO constraints '''

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
		'''
		Iterate over all ports in all resources for the purpose of generating IO constraints,
		flattening multi-bit ports where appropriate
		'''

		for port_name, pin_names, attrs in self.iter_port_constraints():
			if len(pin_names) == 1:
				yield (port_name, pin_names[0], attrs)
			else:
				for bit, pin_name in enumerate(pin_names):
					yield (f'{port_name}[{bit}]', pin_name, attrs)

	def add_clock_constraint(
		self, clock: Signal, frequency: Frequency | int | float, *, src_loc_at: int = 0
	) -> None:
		'''
		Add a clock constraint to the given signal

		Parameters
		----------
		clock: Signal
			The clock signal to constrain

		frequency: Frequency
			The clock frequency to constrain the signal to
		'''

		src_loc = get_src_loc(src_loc_at)

		if not isinstance(clock, Signal):
			raise ToriiSyntaxError(
				f'Object {clock!r} is not a Signal',
				src_loc = src_loc
			)

		if not isinstance(frequency, (Frequency, int, float)):
			raise ToriiSyntaxError(
				'Clock frequency must be a `torii.hdl.time.Frequency`, a `float` or an `int`, not '
				f'an {type(frequency)}',
				src_loc = src_loc
			)

		if isinstance(frequency, (float, int)):
			warn(
				f'Please use a `torii.hdl.time.Frequency` rather than a {type(frequency)} when specifying Clocks',
				DeprecationWarning,
				stacklevel = 2
			)

			frequency = Frequency(frequency)

		if clock in self._clocks:
			freq, loc = self._clocks[clock]
			raise ConstraintError(
				message = (
					f'Cannot add clock constraint of {frequency} to {clock!r}, which is already constrained '
					f'to {freq}'
				),
				src_loc = src_loc,
				additional_ctx = (
					f'Constraint for {freq} was previously applied here:',
					loc
				)
			)

		else:
			self._clocks[clock] = (frequency, src_loc)

	def iter_clock_constraints(self) -> Generator[
		tuple[Signal | None, Signal | None, Frequency], None, None
	]:
		''' Iterate over all clock constraints in all resources, applying back-propagation through the IO buffer '''

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
					raise ToriiSyntaxError(
						f'Expected res.ios[0] to be a \'Pins\' or \'DiffPairs\', not {res.ios[0]!r}',
						src_loc = res.src_loc
					)

		for net_signal, (frequency, _) in self._clocks.items():
			port_signal = pin_i_to_port.get(net_signal)
			yield (net_signal, port_signal, frequency)
