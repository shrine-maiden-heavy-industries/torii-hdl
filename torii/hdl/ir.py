# SPDX-License-Identifier: BSD-2-Clause

from __future__    import annotations

import warnings
from abc           import ABCMeta, abstractmethod
from collections   import OrderedDict, defaultdict
from functools     import cache, reduce
from typing        import TYPE_CHECKING, Literal, TypeAlias

from ..diagnostics import (
	DomainError, DriverConflictWarning, DriverConflictError, ElaborationError, ElaborationWarning, ToriiSyntaxError,
	UnusedElaboratable, NameError
)
from .._typing     import IODirectionIO, SrcLoc
from ..util        import _check_name, flatten
from ..util.string import _get_best_matching
from ..util.tracer import get_src_loc
from ._unused      import MustUse
from .ast          import (
	ClockSignal, ResetSignal, Signal, SignalDict, SignalLikeT, SignalSet, Statement, Value, ValueCastT,
)
from .cd           import ClockDomain

if TYPE_CHECKING:
	from ..build.plat import Platform
	from .dsl         import Module

__all__ = (
	'Elaboratable',
	'Fragment',
	'Instance',
)

class Elaboratable(MustUse, metaclass = ABCMeta):
	'''
	.. todo:: Document Me
	'''

	_MustUse__warning = UnusedElaboratable

	def formal(self, module: Module) -> Module:
		'''
		Entry point for elaboration under formal verification
		'''

		return module

	@abstractmethod
	def elaborate(self, platform: Platform | None) -> Module:
		'''
		.. todo:: Document Me
		'''

		raise NotImplementedError('Elaboratables must implement the \'elaborate\' method')

class Fragment:
	'''
	.. todo:: Document Me
	'''

	@staticmethod
	def get(
		obj: Fragment | Elaboratable, platform: Platform | None,
		*, formal: bool = False, src_loc_at: int = 0
	) -> Fragment:
		'''
		.. todo:: Document Me
		'''

		code = None
		while True:
			if isinstance(obj, Fragment):
				obj._formal = formal
				return obj
			elif isinstance(obj, Elaboratable):
				code = obj.elaborate.__code__
				UnusedElaboratable._MustUse__silence = False
				obj._MustUse__used = True
				new_obj = obj.elaborate(platform)

				if new_obj is not None:
					new_obj._formal = formal

				if formal:
					new_obj = obj.formal(new_obj)
			else:
				raise ElaborationError(
					message = f'Objects of type \'{type(obj).__name__}\' can not be elaborated',
					src_loc = get_src_loc(src_loc_at = 1 + src_loc_at),
					notes = [
						'Only Torii \'Elaboratable\'s and objects that derive from them can be elaborated',
					]
				)

			if new_obj is obj:
				raise ElaborationError(
					message = f'The object {obj!r} recursively elaborates to itself',
					# NOTE(aki):
					# We use this rather than `get_src_loc` because having the diagnostic report from the
					# object location itself rather than the call to `Fragment.get` or wherever up the chain
					# it was makes more sense.
					src_loc = (code.co_filename, code.co_firstlineno),
					notes = [
						'This can occur if the \'elaborate\'  or \'formal\' methods return \'self\' or another instance'
						f'of {type(obj).__name__}.'
					]
				)

			if new_obj is None and code is not None:
				warnings.warn_explicit(
					'\'elaborate()\' method returned None; are you missing a return statement?',
					category = ElaborationWarning,
					filename = code.co_filename,
					lineno = code.co_firstlineno
				)
			obj = new_obj

	def __init__(self) -> None:
		self.ports = SignalDict()
		self.drivers = OrderedDict[str | None, SignalSet]()
		self.first_drivers = dict[str, SrcLoc]()
		self.statements: list[Statement] = []
		self.domains = OrderedDict[str, ClockDomain]()
		self.subfragments = list[tuple[Fragment, str | None]]()
		self.attrs = OrderedDict()
		self.generated = OrderedDict()
		self.flatten = False
		self._formal = False

	def add_ports(self, *ports, dir: IODirectionIO, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		if dir not in ('i', 'o', 'io'):
			raise ToriiSyntaxError(
				f'Expected port direction to be \'i\', \'o\', or \'io\', not \'{dir}\'',
				src_loc = get_src_loc(src_loc_at = src_loc_at)
			)

		for port in flatten(ports):
			self.ports[port] = dir

	def iter_ports(self, dir = None):
		'''
		.. todo:: Document Me
		'''

		if dir is None:
			yield from self.ports
		else:
			for port, port_dir in self.ports.items():
				if port_dir == dir:
					yield port

	def add_driver(self, signal: SignalLikeT | None, domain: str | None = None, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		if domain is not None and (domain == '' or not _check_name(domain)):
			err = ToriiSyntaxError(
				message = (
					'The name for the domain driving the signal must not be empty or contain any control or whitespace '
					'characters'
				),
				src_loc = get_src_loc(),
			)

			if domain == '':
				err.add_note('An empty string was provided to the `domain` parameter, was this intentional?')
			else:
				err.add_note(
					'A character in the domain name was in one of the following Unicode groups: Cc, Cf, Cs, Co, Cn, '
					'Zs, Zl, Zp'
				)

			raise err

		if domain not in self.drivers:
			self.drivers[domain] = SignalSet()
		self.drivers[domain].add(signal)

	def iter_drivers(self):
		'''
		.. todo:: Document Me
		'''

		for domain, signals in self.drivers.items():
			for signal in signals:
				yield domain, signal

	def iter_comb(self):
		'''
		.. todo:: Document Me
		'''

		if None in self.drivers:
			yield from self.drivers[None]

	def iter_sync(self):
		'''
		.. todo:: Document Me
		'''

		for domain, signals in self.drivers.items():
			if domain is None:
				continue
			for signal in signals:
				yield domain, signal

	def iter_signals(self):
		'''
		.. todo:: Document Me
		'''

		signals = SignalSet()
		signals |= self.ports.keys()
		for domain, domain_signals in self.drivers.items():
			if domain is not None:
				cd = self.domains[domain]
				signals.add(cd.clk)
				if cd.rst is not None:
					signals.add(cd.rst)
			signals |= domain_signals
		return signals

	def add_domains(self, *domains, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		for domain in flatten(domains):
			if not isinstance(domain, ClockDomain):
				raise ToriiSyntaxError(
					'Only Torii \'ClockDomain\'s can be added to a fragment, not objects of type'
					f' \'{type(domain).__name__}\'',
					src_loc = get_src_loc(src_loc_at = src_loc_at)
				)

			if domain.name in self.domains:
				raise ToriiSyntaxError(
					f'A clock domain named \'{domain.name}\' already exists within this fragment',
					domain.src_loc,
					additional_ctx = (
						f'The domain \'{domain.name}\' was previously defined here:',
						self.domains[domain.name].src_loc
					),
					notes = [
						'Consider possibly using a \'DomainRenamer\' to rename the colliding domain'
					]
				)

			self.domains[domain.name] = domain

	def iter_domains(self):
		'''
		.. todo:: Document Me
		'''

		yield from self.domains

	def add_statements(self, *stmts, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		for stmt in Statement.cast(stmts, src_loc_at = 1 + src_loc_at):
			stmt._MustUse__used = True
			self.statements.append(stmt)

	def add_subfragment(self, subfragment, name: str | None = None, src_loc_at: int = 0) -> None:
		'''
		.. todo:: Document Me
		'''

		if name is not None and (name == '' or not _check_name(name)):
			err = ToriiSyntaxError(
				'Subfragment names may not be empty or contain any control or whitespace characters',
				src_loc = get_src_loc(src_loc_at = src_loc_at),
			)

			if name == '':
				err.add_note('An empty string was provided to the \'type\' parameter, was this intentional?')
			else:
				err.add_note(
					'A character in the type was in one of the following Unicode groups: Cc, Cf, Cs, Co, Cn, Zs,'
					' Zl, Zp'
				)

			raise err

		if not isinstance(subfragment, Fragment):
			raise ToriiSyntaxError(
				'Only Torii \'Fragment\'s may be added as a subfragment, not objects of type'
				f' \'{type(subfragment).__name__}\'',
				src_loc = get_src_loc(src_loc_at = src_loc_at)
			)

		self.subfragments.append((subfragment, name))

	def find_subfragment(self, name_or_index, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		if isinstance(name_or_index, int):
			if name_or_index < len(self.subfragments):
				subfragment, name = self.subfragments[name_or_index]
				return subfragment

			raise NameError(
				message = f'No subfragment at index #{name_or_index}',
				src_loc = get_src_loc(src_loc_at = src_loc_at)
			)
		else:
			for subfragment, name in self.subfragments:
				if name == name_or_index:
					return subfragment

			raise NameError(
				message = f'No subfragment with name \'{name_or_index}\'',
				src_loc = get_src_loc(src_loc_at = src_loc_at)
			)

	def find_generated(self, *path, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		if len(path) > 1:
			path_component, *path = path
			return self.find_subfragment(
					path_component,
					src_loc_at = 1 + src_loc_at
				).find_generated(
					*path,
					src_loc_at = 1 + src_loc_at
				)
		else:
			item, = path
			return self.generated[item]

	def elaborate(self, platform):
		'''
		.. todo:: Document Me
		'''

		return self

	def _merge_subfragment(self, subfragment, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		# Merge subfragment's everything except clock domains into this fragment.
		# Flattening is done after clock domain propagation, so we can assume the domains
		# are already the same in every involved fragment in the first place.
		self.ports.update(subfragment.ports)
		self.first_drivers.update(subfragment.first_drivers)
		for domain, signal in subfragment.iter_drivers():
			self.add_driver(signal, domain, src_loc_at = 1 + src_loc_at)
		self.statements += subfragment.statements
		self.subfragments += subfragment.subfragments

		# Remove the merged subfragment.
		found = False
		for i, (check_subfrag, check_name) in enumerate(self.subfragments): # :nobr:
			if subfragment == check_subfrag:
				del self.subfragments[i]
				found = True
				break
		if not found:
			raise ElaborationError('Unable to find merged subfragment!')

	def _resolve_hierarchy_conflicts(self, hierarchy = ('top',), mode = 'warn', *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		# TODO(aki): I don't think `silent` should ever be used, seems a bit ridiculous
		if mode not in ('silent', 'warn', 'error'):
			raise ValueError(f'Expected mode to be one of \'silent\', \'warn\', or \'error\', not \'{mode!r}\'')

		driver_subfrags = SignalDict()

		def add_subfrag(registry, entity, entry):
			# Because of missing domain insertion, at the point when this code runs, we have
			# a mixture of bound and unbound {Clock,Reset}Signals. Map the bound ones to
			# the actual signals (because the signal itself can be driven as well); but leave
			# the unbound ones as it is, because there's no concrete signal for it yet anyway.
			if isinstance(entity, ClockSignal) and entity.domain in self.domains:
				entity = self.domains[entity.domain].clk
			elif isinstance(entity, ResetSignal) and entity.domain in self.domains:
				entity = self.domains[entity.domain].rst

			if entity not in registry:
				registry[entity] = set()
			registry[entity].add(entry)

		# For each signal driven by this fragment and/or its subfragments, determine which
		# subfragments also drive it.
		for domain, signal in self.iter_drivers():
			add_subfrag(driver_subfrags, signal, (None, hierarchy))

		flatten_subfrags = set()
		for i, (subfrag, name) in enumerate(self.subfragments):
			if name is None:
				name = f'<unnamed #{i}>'
			subfrag_hierarchy = hierarchy + (name,)

			if subfrag.flatten:
				# Always flatten subfragments that explicitly request it.
				flatten_subfrags.add((subfrag, subfrag_hierarchy))

			if isinstance(subfrag, Instance):
				# Never flatten instances.
				continue

			# First, recurse into subfragments and let them detect driver conflicts as well.
			subfrag_drivers = subfrag._resolve_hierarchy_conflicts(
				subfrag_hierarchy, mode, src_loc_at = 1 + src_loc_at
			)

			# Second, classify subfragments by signals they drive.
			for signal in subfrag_drivers:
				add_subfrag(driver_subfrags, signal, (subfrag, subfrag_hierarchy))

		# Find out the set of subfragments that needs to be flattened into this fragment
		# to resolve driver-driver conflicts.
		def flatten_subfrags_if_needed(subfrags):
			if len(subfrags) == 1:
				return []
			flatten_subfrags.update((f, h) for f, h in subfrags if f is not None)
			return list(sorted('.'.join(h) for f, h in subfrags))

		for signal, subfrags in driver_subfrags.items():
			subfrag_names = flatten_subfrags_if_needed(subfrags)
			if not subfrag_names:
				continue

			# While we're at it, show a message.
			message = f'Signal \'{signal}\' is driven from multiple fragments: {", ".join(subfrag_names)}'
			if mode == 'error':
				raise DriverConflictError(
					message = message,
					src_loc = signal.src_loc
				)
			elif mode == 'warn':
				message += '; hierarchy will be flattened'
				warnings.warn_explicit(
					message,
					DriverConflictWarning,
					filename = signal.src_loc[0],
					lineno   = signal.src_loc[1]
				)

		# Flatten hierarchy.
		for subfrag, subfrag_hierarchy in sorted(flatten_subfrags, key = lambda x: x[1]):
			self._merge_subfragment(subfrag, src_loc_at = 1 + src_loc_at)

		# If we flattened anything, we might be in a situation where we have a driver conflict
		# again, e.g. if we had a tree of fragments like A --- B --- C where only fragments
		# A and C were driving a signal S. In that case, since B is not driving S itself,
		# processing B will not result in any flattening, but since B is transitively driving S,
		# processing A will flatten B into it. Afterwards, we have a tree like AB --- C, which
		# has another conflict.
		if any(flatten_subfrags):
			# Try flattening again.
			return self._resolve_hierarchy_conflicts(hierarchy, mode, src_loc_at = 1 + src_loc_at)

		# Nothing was flattened, we're done!
		return SignalSet(driver_subfrags.keys())

	def _propagate_domains_up(self, hierarchy = ('top',), *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		from .xfrm import DomainRenamer

		domain_subfrags = defaultdict(set)

		# For each domain defined by a subfragment, determine which subfragments define it.
		for i, (subfrag, name) in enumerate(self.subfragments):
			# First, recurse into subfragments and let them propagate domains up as well.
			hier_name = name
			if hier_name is None:
				hier_name = f'<unnamed #{i}>'
			subfrag._propagate_domains_up(hierarchy + (hier_name,), src_loc_at = 1 + src_loc_at)

			# Second, classify subfragments by domains they define.
			for domain_name, domain in subfrag.domains.items():
				if domain.local:
					continue
				domain_subfrags[domain_name].add((subfrag, name, i))

		# For each domain defined by more than one subfragment, rename the domain in each
		# of the subfragments such that they no longer conflict.
		for domain_name, subfrags in domain_subfrags.items():
			if len(subfrags) == 1:
				continue

			names = [n for f, n, i in subfrags]
			if not all(names):
				names = sorted(f'<unnamed #{i}>' if n is None else f'\'{n}\'' for f, n, i in subfrags)
				raise DomainError(
					message = (
						f'Domain \'{domain_name}\' is defined by subfragments {", ".join(names)} of fragment '
						f'\'{".".join(hierarchy)}\'; it is necessary to either rename subfragment domains '
						'explicitly, or give names to subfragments'
					),
					src_loc = get_src_loc(src_loc_at = src_loc_at)
				)

			if len(names) != len(set(names)):
				names = sorted(f'#{i}' for f, n, i in subfrags)
				raise DomainError(
					message = (
						f'Domain \'{domain_name}\' is defined by subfragments {", ".join(names)} of fragment '
						f'\'{".".join(hierarchy)}\', some of which have identical names; it is necessary to either '
						'rename subfragment domains explicitly, or give distinct names to subfragments'
					),
					src_loc = get_src_loc(src_loc_at = src_loc_at)
				)

			for subfrag, name, i in subfrags:
				domain_name_map = { domain_name: f'{name}_{domain_name}' }
				# XXX(aki):
				# I suspect this will cause some weird source locality offsetting, i've not found
				# any so far, but I have a strong suspicion that it will eventually.
				self.subfragments[i] = (DomainRenamer(**domain_name_map)(subfrag), name)

		# Finally, collect the (now unique) subfragment domains, and merge them into our domains.
		for subfrag, name in self.subfragments:
			self.first_drivers.update(subfrag.first_drivers)
			for domain_name, domain in subfrag.domains.items():
				if domain.local:
					continue
				self.add_domains(domain, src_loc_at = 1 + src_loc_at)

	def _propagate_domains_down(self, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		# For each domain defined in this fragment, ensure it also exists in all subfragments.
		for subfrag, name in self.subfragments:
			subfrag.first_drivers.update(self.first_drivers)
			for domain in self.iter_domains():
				if domain in subfrag.domains:
					if self.domains[domain] is not subfrag.domains[domain]:
						raise ElaborationError(
							message = (
								f'Subfragment domain propagation failure, mismatching domains: '
								f'{self.domains[domain]!r} is not {subfrag.domains[domain]!r}'
							),
							src_loc = get_src_loc(src_loc_at = src_loc_at)
						)
				else:
					subfrag.add_domains(self.domains[domain], src_loc_at = 1 + src_loc_at)

			subfrag._propagate_domains_down(src_loc_at = 1 + src_loc_at)

	def _create_missing_domains(self, missing_domain, *, platform = None, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		from .xfrm import DomainCollector

		collector = DomainCollector()
		collector(self)

		new_domains = []
		for domain_name in collector.used_domains - collector.defined_domains:
			if domain_name is None:
				continue
			value = missing_domain(domain_name)
			if value is None:
				matches = _get_best_matching(domain_name, collector.defined_domains | { 'sync', 'comb' })
				additional_ctx = None

				if len(matches) > 0:
					match = matches[0]
					msg = f'The clock domain \'{domain_name}\' was used but not defined, did you mean \'{match}\'?'
					if match not in ('sync', 'comb'):
						additional_ctx = (
							f'The clock domain \'{match}\' was defined here:',
							self.domains[match].src_loc
						)
				else:
					msg = f'The clock domain \'{domain_name}\' was used but not defined'

				raise ToriiSyntaxError(
					msg,
					# BUG(aki):
					# In the case where the domain is not defined, this will return `None`,
					# which causes our diagnostics to be weird, there are possibly two ways
					# to fix this:
					#  1. Add tracking to where the first `add_driver` for the domain was called
					#     so we have source locality information for at least that
					#  2. Use `src_loc_at` up the chain to at least raise this error where call that
					#     caused this to explode was.
					#
					# I've opted for option number 2 for now, but I think maybe option 1 would be
					# "better", for some definition of better.
					src_loc = self.first_drivers.get(domain_name),
					notes = [
						'The platform function that is used to generate missing domains did not generate a'
						f' domain called \'{domain_name}\''
					],
					additional_ctx = additional_ctx
				)

			if type(value) is ClockDomain:
				self.add_domains(value, src_loc_at = 1 + src_loc_at)
				# And expose ports on the newly added clock domain, since it is added directly
				# and there was no chance to add any logic driving it.
				new_domains.append(value)
			else:
				new_fragment = Fragment.get(value, platform = platform)
				if domain_name not in new_fragment.domains:
					defined = new_fragment.domains.keys()

					if code := missing_domain.__code__:
						missing_domain_src_loc = (code.co_filename, code.co_firstlineno)
					else:
						missing_domain_src_loc = None

					raise DomainError(
						message = (
							'Fragment returned by missing domain callback does not define '
							f'requested domain \'{domain_name}\' (defines {", ".join(f"`{n}`" for n in defined)}).'
						),
						src_loc = missing_domain_src_loc
					)

				self.add_subfragment(new_fragment, f'cd_{domain_name}', src_loc_at = 1 + src_loc_at)
				self.add_domains(new_fragment.domains.values(), src_loc_at = 1 + src_loc_at)
		return new_domains

	def _propagate_domains(self, missing_domain, *, platform = None, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		self._propagate_domains_up(src_loc_at = 1 + src_loc_at)
		self._propagate_domains_down(src_loc_at = 1 + src_loc_at)
		self._resolve_hierarchy_conflicts(src_loc_at = 1 + src_loc_at)
		new_domains = self._create_missing_domains(missing_domain, platform = platform, src_loc_at = 1 + src_loc_at)
		self._propagate_domains_down(src_loc_at = 1 + src_loc_at)
		return new_domains

	def _prepare_use_def_graph(self, parent, level, uses, defs, ios, top, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		def add_uses(*sigs, self = self):
			for sig in flatten(sigs):
				if sig not in uses:
					uses[sig] = set()
				uses[sig].add(self)

		def add_defs(*sigs):
			for sig in flatten(sigs):
				if sig not in defs:
					defs[sig] = self
				else:
					assert defs[sig] is self

		def add_io(*sigs):
			for sig in flatten(sigs):
				if sig not in ios:
					ios[sig] = self
				else:
					assert ios[sig] is self

		# Collect all signals we're driving (on LHS of statements), and signals we're using
		# (on RHS of statements, or in clock domains).
		for stmt in self.statements:
			add_uses(stmt._rhs_signals())
			add_defs(stmt._lhs_signals())

		for domain, _ in self.iter_sync():
			cd = self.domains[domain]
			add_uses(cd.clk)
			if cd.rst is not None:
				add_uses(cd.rst)

		# Repeat for subfragments.
		for subfrag, name in self.subfragments:
			if isinstance(subfrag, Instance):
				for port_name, (value, dir) in subfrag.named_ports.items():
					if dir == 'i':
						# Prioritize defs over uses.
						rhs_without_outputs = value._rhs_signals() - subfrag.iter_ports(dir = 'o')
						subfrag.add_ports(rhs_without_outputs, dir = dir)
						add_uses(value._rhs_signals())
					if dir == 'o':
						subfrag.add_ports(value._lhs_signals(), dir = dir)
						add_defs(value._lhs_signals())
					if dir == 'io':
						subfrag.add_ports(value._lhs_signals(), dir = dir)
						add_io(value._lhs_signals())
			else:
				parent[subfrag] = self
				level[subfrag]  = level[self] + 1

				subfrag._prepare_use_def_graph(parent, level, uses, defs, ios, top, src_loc_at = 1 + src_loc_at)

	def _propagate_ports(self, ports, all_undef_as_ports, *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		# Take this fragment graph:
		#
		#    __ B (def: q, use: p r)
		#   /
		#  A (def: p, use: q r)
		#   \
		#    \_ C (def: r, use: p q)
		#
		# We need to consider three cases.
		#   1. Signal p requires an input port in B;
		#   2. Signal r requires an output port in C;
		#   3. Signal r requires an output port in C and an input port in B.
		#
		# Adding these ports can be in general done in three steps for each signal:
		#   1. Find the least common ancestor of all uses and defs.
		#   2. Going upwards from the single def, add output ports.
		#   3. Going upwards from all uses, add input ports.

		parent = { self: None }
		level  = { self: 0 }
		uses   = SignalDict()
		defs   = SignalDict()
		ios    = SignalDict()
		self._prepare_use_def_graph(parent, level, uses, defs, ios, self, src_loc_at = 1 + src_loc_at)

		ports = SignalSet(ports)
		if all_undef_as_ports:
			for sig in uses:
				if sig in defs:
					continue
				ports.add(sig)
		for sig in ports:
			if sig not in uses:
				uses[sig] = set()
			uses[sig].add(self)

		@cache
		def lca_of(fragu, fragv):
			# Normalize fragu to be deeper than fragv.
			if level[fragu] < level[fragv]:
				fragu, fragv = fragv, fragu
			# Find ancestor of fragu on the same level as fragv.
			for _ in range(level[fragu] - level[fragv]):
				fragu = parent[fragu]
			# If fragv was the ancestor of fragv, we're done.
			if fragu == fragv:
				return fragu
			# Otherwise, they are at the same level but in different branches. Step both fragu
			# and fragv until we find the common ancestor.
			while parent[fragu] != parent[fragv]:
				fragu = parent[fragu]
				fragv = parent[fragv]
			return parent[fragu]

		for sig in uses:
			if sig in defs:
				lca  = reduce(lca_of, uses[sig], defs[sig])
			else:
				lca  = reduce(lca_of, uses[sig])

			for frag in uses[sig]:
				if sig in defs and frag is defs[sig]:
					continue
				while frag != lca:
					frag.add_ports(sig, dir = 'i', src_loc_at = 1 + src_loc_at)
					frag = parent[frag]

			if sig in defs:
				frag = defs[sig]
				while frag != lca:
					frag.add_ports(sig, dir = 'o', src_loc_at = 1 + src_loc_at)
					frag = parent[frag]

		for sig in ios:
			frag = ios[sig]
			while frag is not None:
				frag.add_ports(sig, dir = 'io', src_loc_at = 1 + src_loc_at)
				frag = parent[frag]

		for sig in ports:
			if sig in ios:
				continue
			if sig in defs:
				self.add_ports(sig, dir = 'o', src_loc_at = 1 + src_loc_at)
			else:
				self.add_ports(sig, dir = 'i', src_loc_at = 1 + src_loc_at)

	def prepare(self, ports = None, missing_domain = lambda name: ClockDomain(name), *, src_loc_at: int = 0):
		'''
		.. todo:: Document Me
		'''

		from .xfrm import DomainLowerer, SampleLowerer

		fragment = SampleLowerer(formal = self._formal)(self)
		new_domains = fragment._propagate_domains(missing_domain, src_loc_at = 1 + src_loc_at)
		fragment = DomainLowerer()(fragment)
		if ports is None:
			fragment._propagate_ports(ports = (), all_undef_as_ports = True, src_loc_at = 1 + src_loc_at)
		else:
			# TODO(aki): Maybe ports should be an `Iterable[Signal]`?
			if not isinstance(ports, tuple) and not isinstance(ports, list):
				err = ToriiSyntaxError(
					'The \'ports\' parameter must be a list or a tuple of signals, not an object of type'
					f' \'{type(ports).__name__}\'',
					src_loc = get_src_loc(src_loc_at = src_loc_at)
				)

				if isinstance(ports, Value):
					err.add_note(
						'It looks as if you did \'ports = <signal>\' rather than \'ports = (<signal>,)\','
						' was this intentional?'
					)

				raise err
			mapped_ports = []
			# Lower late bound signals like ClockSignal() to ports.
			port_lowerer = DomainLowerer(fragment.domains)
			for port in ports:
				if not isinstance(port, (Signal, ClockSignal, ResetSignal)):
					raise ToriiSyntaxError(
						f'Only Torii signals may be added as ports, not objects of type \'{type(port).__name__}\'',
						src_loc = get_src_loc(src_loc_at = src_loc_at),
						notes = [
							'The valid signal types are \'Signal\', \'ClockSignal\', and \'ResetSignal\''
						]
					)
				mapped_ports.append(port_lowerer.on_value(port))
			# Add ports for all newly created missing clock domains, since not doing so defeats
			# the purpose of domain auto-creation. (It's possible to refer to these ports before
			# the domain actually exists through late binding, but it's inconvenient.)
			for cd in new_domains:
				mapped_ports.append(cd.clk)
				if cd.rst is not None:
					mapped_ports.append(cd.rst)
			fragment._propagate_ports(ports = mapped_ports, all_undef_as_ports = False, src_loc_at = 1 + src_loc_at)
		return fragment

	def _assign_names_to_signals(self, *, src_loc_at: int = 0) -> SignalDict[str]:
		'''
		Assign names to signals used in this fragment.

		Returns
		-------
		SignalDict[str]
			A mapping from signals used in this fragment to their local names. Because names are
			deduplicated using local information only, the same signal used in a different fragment
			may get a different name.
		'''

		signal_names   = SignalDict[str]()
		assigned_names = set()

		def add_signal_name(signal: Signal):
			if signal not in signal_names:
				if signal.name not in assigned_names:
					name = signal.name
				else:
					name = f'{signal.name}${len(assigned_names)}'
					assert name not in assigned_names
				signal_names[signal] = name
				assigned_names.add(name)

		for port in self.ports.keys():
			add_signal_name(port)

		for domain_name, _ in self.drivers.items():
			if domain_name is not None:
				domain = self.domains[domain_name]
				add_signal_name(domain.clk)
				if domain.rst is not None:
					add_signal_name(domain.rst)

		for statement in self.statements:
			for signal in statement._lhs_signals() | statement._rhs_signals():
				if not isinstance(signal, (ClockSignal, ResetSignal)):
					add_signal_name(signal)

		return signal_names

	def _assign_names_to_fragments(
		self, hierarchy: tuple[str, ...] = ('top',), *, _names: dict[Fragment, tuple[str, ...]] | None = None,
		src_loc_at: int = 0
	):
		'''
		Assign names to this fragment and its subfragments.

		Subfragments may not necessarily have a name. This method assigns every such subfragment
		a name, ``U$<number>``, where ``<number>`` is based on its location in the hierarchy.

		Subfragment names may collide with signal names safely in Torii, but this may confuse
		backends. This method assigns every such subfragment a name, ``<name>$U$<number>``, where
		``name`` is its original name, and ``<number>`` is based on its location in the hierarchy.

		Parameters
		----------
		hierarchy: tuple[str, ...]
			Name of this fragment.

		Returns
		-------
		dict[Fragment, tuple[str, ...]]
			A mapping from this fragment and its subfragments to their full hierarchical names.
		'''

		if _names is None:
			_names = dict[Fragment, tuple[str, ...]]()
		_names[self] = hierarchy

		signal_names = set(self._assign_names_to_signals(src_loc_at = 1 + src_loc_at).values())
		for subfragment_index, (subfragment, subfragment_name) in enumerate(self.subfragments):
			if subfragment_name is None:
				subfragment_name = f'U${subfragment_index}'
			elif subfragment_name in signal_names:
				subfragment_name = f'{subfragment_name}$U${subfragment_index}'
			assert subfragment_name not in signal_names
			subfragment._assign_names_to_fragments(
				hierarchy = (*hierarchy, subfragment_name), _names = _names, src_loc_at = 1 + src_loc_at
			)

		return _names

InstanceArgsT: TypeAlias = tuple[Literal['a', 'p'] | IODirectionIO, str, ValueCastT]

class Instance(Fragment):
	'''
	Allows for the direct instantiation of external modules, cells, or primitives.

	It accepts the name of the object to instantiate and a collection of keyword arguments
	that define the ports, attributes, and parameters to it.

	It is defined by a prefix followed by the canonical name of the element the value is setting.
	For instance, if you have a cell called ``dff`` with ports named ``CLK``, ``D``, and ``Q`` you
	are able to instantiate it as follows:

	.. code-block:: python

		dff = Instance(
			'dff',
			i_D   = sig_in,
			i_CLK = clk,
			o_Q   = sig_out,
		)

	The meaning of the prefix for the arguments are as follows:

	+---------+----------------------------+
	| Prefix  | Corresponding Type         |
	+=========+============================+
	| ``a_``  | Attribute                  |
	+---------+----------------------------+
	| ``p_``  | Parameter                  |
	+---------+----------------------------+
	| ``i_``  | Input Port/Signal          |
	+---------+----------------------------+
	| ``o_``  | Output Port/Signal         |
	+---------+----------------------------+
	| ``io_`` | Bi-directional Port/Signal |
	+---------+----------------------------+

	Parameters
	----------
	type: str
		The name/type of object to instantiate
	'''

	def __init__(
		self, type: str, *args: InstanceArgsT, src_loc: SrcLoc | None = None, src_loc_at: int = 0,
		**kwargs: ValueCastT | str
	) -> None:
		super().__init__()

		if type == '' or not _check_name(type):
			raise NameError('Instance type must not be empty or contain any control or whitespace characters')

		self.type        = type
		self.parameters  = OrderedDict[str, 'ValueCastT | str']()
		self.named_ports = OrderedDict[str, tuple[Value, IODirectionIO]]()
		self.src_loc     = src_loc or get_src_loc(src_loc_at)

		for (kind, name, value) in args:
			if kind == 'a':
				self.attrs[name] = value
			elif kind == 'p':
				self.parameters[name] = value
			elif kind in ('i', 'o', 'io'):
				self.named_ports[name] = (Value.cast(value), kind)
			else:
				raise NameError(
					f'Instance argument {(kind, name, value)!r} should be a tuple (kind, name, value) '
					'where kind is one of \'a\', \'p\', \'i\', \'o\', or \'io\''
				)

		for kw, arg in kwargs.items():
			if not _check_name(kw):
				raise NameError('Instance parameter must not contain any control or whitespace characters')

			if kw.startswith(('i_', 'o_', 'io_')) and isinstance(arg, str):
				raise TypeError(
					'The argument for \'i_\', \'o_\', or \'io_\', parameters to an'
					f'Instance must be a valid Value castable type, not \'{arg!r}\''
				)

			if kw.startswith('a_'):
				self.attrs[kw[2:]] = arg
			elif kw.startswith('p_'):
				self.parameters[kw[2:]] = arg
			elif kw.startswith('i_'):
				assert not isinstance(arg, str)
				self.named_ports[kw[2:]] = (Value.cast(arg), 'i')
			elif kw.startswith('o_'):
				assert not isinstance(arg, str)
				self.named_ports[kw[2:]] = (Value.cast(arg), 'o')
			elif kw.startswith('io_'):
				assert not isinstance(arg, str)
				self.named_ports[kw[3:]] = (Value.cast(arg), 'io')
			else:
				raise NameError(
					f'Instance keyword argument {kw} = {arg!r} does not start with one of '
					'\'a_\', \'p_\', \'i_\', \'o_\', or \'io_\''
				)
