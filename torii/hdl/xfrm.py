# SPDX-License-Identifier: BSD-2-Clause

from abc             import ABCMeta, abstractmethod
from collections     import OrderedDict
from collections.abc import Iterable
from copy            import copy

from ..util          import flatten, tracer
from .ast            import (
	AnyValue, ArrayProxy, Assign, Cat, ClockSignal, Const, Initial, Mux, Operator, Part, Property, ResetSignal, Sample,
	Signal, SignalDict, SignalSet, Slice, Statement, Switch, Value, ValueDict, _StatementList,
)
from .cd             import DomainError
from .ir             import Elaboratable, Fragment, Instance
from .mem            import MemoryInstance

__all__ = (
	'DomainCollector',
	'DomainLowerer',
	'DomainRenamer',
	'EnableInserter',
	'FragmentTransformer',
	'LHSGroupAnalyzer',
	'LHSGroupFilter',
	'ResetInserter',
	'SampleDomainInjector',
	'SampleLowerer',
	'StatementTransformer',
	'StatementVisitor',
	'SwitchCleaner',
	'TransformedElaboratable',
	'ValueTransformer',
	'ValueVisitor',
)

class ValueVisitor(metaclass = ABCMeta):
	@abstractmethod
	def on_Const(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Signal(self, value):
		pass # :nocov:

	@abstractmethod
	def on_ClockSignal(self, value):
		pass # :nocov:

	@abstractmethod
	def on_ResetSignal(self, value):
		pass # :nocov:

	@abstractmethod
	def on_AnyValue(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Operator(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Slice(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Part(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Cat(self, value):
		pass # :nocov:

	@abstractmethod
	def on_ArrayProxy(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Sample(self, value):
		pass # :nocov:

	@abstractmethod
	def on_Initial(self, value):
		pass # :nocov:

	def on_unknown_value(self, value):
		raise TypeError(f'Cannot transform value {value!r}') # :nocov:

	def replace_value_src_loc(self, value, new_value):
		return True

	def on_value(self, value):
		if type(value) is Const:
			new_value = self.on_Const(value)
		elif type(value) is Signal:
			new_value = self.on_Signal(value)
		elif type(value) is ClockSignal:
			new_value = self.on_ClockSignal(value)
		elif type(value) is ResetSignal:
			new_value = self.on_ResetSignal(value)
		elif type(value) is AnyValue:
			new_value = self.on_AnyValue(value)
		elif type(value) is Operator:
			new_value = self.on_Operator(value)
		elif type(value) is Slice:
			new_value = self.on_Slice(value)
		elif type(value) is Part:
			new_value = self.on_Part(value)
		elif type(value) is Cat:
			new_value = self.on_Cat(value)
		elif type(value) is ArrayProxy:
			new_value = self.on_ArrayProxy(value)
		elif type(value) is Sample:
			new_value = self.on_Sample(value)
		elif type(value) is Initial:
			new_value = self.on_Initial(value)
		else:
			new_value = self.on_unknown_value(value)
		if isinstance(new_value, Value) and self.replace_value_src_loc(value, new_value):
			new_value.src_loc = value.src_loc
		return new_value

	def __call__(self, value):
		return self.on_value(value)

class ValueTransformer(ValueVisitor):
	def on_Const(self, value):
		return value

	def on_Signal(self, value):
		return value

	def on_ClockSignal(self, value):
		return value

	def on_ResetSignal(self, value):
		return value

	def on_AnyValue(self, value):
		return value

	def on_Operator(self, value):
		return Operator(value.operator, [ self.on_value(o) for o in value.operands ])

	def on_Slice(self, value):
		return Slice(self.on_value(value.value), value.start, value.stop)

	def on_Part(self, value):
		return Part(self.on_value(value.value), self.on_value(value.offset), value.width, value.stride)

	def on_Cat(self, value):
		return Cat(self.on_value(o) for o in value.parts)

	def on_ArrayProxy(self, value):
		return ArrayProxy(
			[self.on_value(elem) for elem in value._iter_as_values()],
			self.on_value(value.index)
		)

	def on_Sample(self, value):
		return Sample(self.on_value(value.value), value.clocks, value.domain)

	def on_Initial(self, value):
		return value

class StatementVisitor(metaclass = ABCMeta):
	@abstractmethod
	def on_Assign(self, stmt):
		pass # :nocov:

	@abstractmethod
	def on_Property(self, stmt):
		pass # :nocov:

	@abstractmethod
	def on_Switch(self, stmt):
		pass # :nocov:

	@abstractmethod
	def on_statements(self, stmts):
		pass # :nocov:

	def on_unknown_statement(self, stmt):
		raise TypeError(f'Cannot transform statement {stmt!r}') # :nocov:

	def replace_statement_src_loc(self, stmt, new_stmt):
		return True

	def on_statement(self, stmt):
		if type(stmt) is Assign:
			new_stmt = self.on_Assign(stmt)
		elif type(stmt) is Property:
			new_stmt = self.on_Property(stmt)
		elif isinstance(stmt, Switch):
			# Uses `isinstance()` and not `type() is` because amaranth.compat requires it.
			new_stmt = self.on_Switch(stmt)
		elif isinstance(stmt, Iterable):
			new_stmt = self.on_statements(stmt)
		else:
			new_stmt = self.on_unknown_statement(stmt)
		if isinstance(new_stmt, Statement) and self.replace_statement_src_loc(stmt, new_stmt):
			new_stmt.src_loc = stmt.src_loc
			if isinstance(new_stmt, Switch) and isinstance(stmt, Switch):
				new_stmt.case_src_locs = stmt.case_src_locs
		if isinstance(new_stmt, Property):
			new_stmt._MustUse__used = True
		return new_stmt

	def __call__(self, stmt):
		return self.on_statement(stmt)

class StatementTransformer(StatementVisitor):
	def on_value(self, value):
		return value

	def on_Assign(self, stmt):
		return Assign(self.on_value(stmt.lhs), self.on_value(stmt.rhs))

	def on_Property(self, stmt):
		return Property(
			stmt.kind, self.on_value(stmt.test), _check = stmt._check,
			_en = stmt._en, name = stmt.name
		)

	def on_Switch(self, stmt):
		cases = OrderedDict((k, self.on_statement(s)) for k, s in stmt.cases.items())
		return Switch(self.on_value(stmt.test), cases)

	def on_statements(self, stmts):
		return _StatementList(flatten(self.on_statement(stmt) for stmt in stmts))

class FragmentTransformer:
	def map_subfragments(self, fragment, new_fragment):
		for subfragment, name in fragment.subfragments:
			new_fragment.add_subfragment(self(subfragment), name)

	def map_ports(self, fragment, new_fragment):
		for port, dir in fragment.ports.items():
			new_fragment.add_ports(port, dir = dir)

	def map_named_ports(self, fragment, new_fragment):
		if hasattr(self, 'on_value'):
			for name, (value, dir) in fragment.named_ports.items():
				new_fragment.named_ports[name] = self.on_value(value), dir
		else:
			new_fragment.named_ports = OrderedDict(fragment.named_ports.items())

	def map_domains(self, fragment, new_fragment):
		for domain in fragment.iter_domains():
			new_fragment.add_domains(fragment.domains[domain])

	def map_statements(self, fragment, new_fragment):
		if hasattr(self, 'on_statement'):
			new_fragment.add_statements(map(self.on_statement, fragment.statements))
		else:
			new_fragment.add_statements(fragment.statements)

	def map_drivers(self, fragment, new_fragment):
		for domain, signal in fragment.iter_drivers():
			new_fragment.add_driver(signal, domain)

	def map_memory_ports(self, fragment, new_fragment):
		new_fragment.read_ports = [
			copy(port) for port in fragment.read_ports
		]

		new_fragment.write_ports = [
			copy(port) for port in fragment.write_ports
		]

		if hasattr(self, 'on_value'):
			for port in new_fragment.read_ports:
				port.en   = self.on_value(port.en)
				port.addr = self.on_value(port.addr)
				port.data = self.on_value(port.data)

			for port in new_fragment.write_ports:
				port.en   = self.on_value(port.en)
				port.addr = self.on_value(port.addr)
				port.data = self.on_value(port.data)

	def on_fragment(self, fragment):
		if isinstance(fragment, MemoryInstance):
			new_fragment = MemoryInstance(fragment.memory, [], [])
			self.map_memory_ports(fragment, new_fragment)
		elif isinstance(fragment, Instance):
			new_fragment = Instance(fragment.type, src_loc = fragment.src_loc)
			new_fragment.parameters = OrderedDict(fragment.parameters)
			self.map_named_ports(fragment, new_fragment)
		else:
			new_fragment = Fragment()
			new_fragment.flatten = fragment.flatten
		new_fragment.attrs = OrderedDict(fragment.attrs)
		self.map_ports(fragment, new_fragment)
		self.map_subfragments(fragment, new_fragment)
		self.map_domains(fragment, new_fragment)
		self.map_statements(fragment, new_fragment)
		self.map_drivers(fragment, new_fragment)
		return new_fragment

	def __call__(self, value, *, src_loc_at = 0):
		if isinstance(value, Fragment):
			return self.on_fragment(value)
		elif isinstance(value, TransformedElaboratable):
			value._transforms_.append(self)
			return value
		elif hasattr(value, 'elaborate'):
			value = TransformedElaboratable(value, src_loc_at = 1 + src_loc_at)
			value._transforms_.append(self)
			return value
		else:
			raise AttributeError(f'Object {value!r} cannot be elaborated')

class TransformedElaboratable(Elaboratable):
	def __init__(self, elaboratable, *, src_loc_at = 0) -> None:
		if not hasattr(elaboratable, 'elaborate'):
			raise TypeError(f'Unable to elaborate object of type \'{type(elaboratable)}\' which has no \'elaborate\' method')

		# Fields prefixed and suffixed with underscore to avoid as many conflicts with the inner
		# object as possible, since we're forwarding attribute requests to it.
		self._elaboratable_ = elaboratable
		self._transforms_   = []

	def __getattr__(self, attr):
		return getattr(self._elaboratable_, attr)

	def elaborate(self, platform):
		fragment = Fragment.get(self._elaboratable_, platform)
		for transform in self._transforms_:
			fragment = transform(fragment)
		return fragment

class DomainCollector(ValueVisitor, StatementVisitor):
	def __init__(self) -> None:
		self.used_domains = set()
		self.defined_domains = set()
		self._local_domains = set()

	def _add_used_domain(self, domain_name):
		if domain_name is None:
			return
		if domain_name in self._local_domains:
			return
		self.used_domains.add(domain_name)

	def on_ignore(self, value):
		pass

	on_Const = on_ignore
	on_Signal = on_ignore
	on_AnyValue = on_ignore

	def on_ClockSignal(self, value):
		self._add_used_domain(value.domain)

	def on_ResetSignal(self, value):
		self._add_used_domain(value.domain)

	def on_Operator(self, value):
		for o in value.operands:
			self.on_value(o)

	def on_Slice(self, value):
		self.on_value(value.value)

	def on_Part(self, value):
		self.on_value(value.value)
		self.on_value(value.offset)

	def on_Cat(self, value):
		for o in value.parts:
			self.on_value(o)

	def on_ArrayProxy(self, value):
		for elem in value._iter_as_values():
			self.on_value(elem)
		self.on_value(value.index)

	def on_Sample(self, value):
		self.on_value(value.value)

	def on_Initial(self, value):
		pass

	def on_Assign(self, stmt):
		self.on_value(stmt.lhs)
		self.on_value(stmt.rhs)

	def on_Property(self, stmt):
		self.on_value(stmt.test)

	def on_Switch(self, stmt):
		self.on_value(stmt.test)
		for stmts in stmt.cases.values():
			self.on_statement(stmts)

	def on_statements(self, stmts):
		for stmt in stmts:
			self.on_statement(stmt)

	def on_fragment(self, fragment):
		if isinstance(fragment, MemoryInstance):
			for port in fragment.read_ports:
				self.on_value(port.addr)
				self.on_value(port.data)
				self.on_value(port.en)
				if port.domain != 'comb':
					self._add_used_domain(port.domain)

			for port in fragment.write_ports:
				self.on_value(port.addr)
				self.on_value(port.data)
				self.on_value(port.en)
				self._add_used_domain(port.domain)

		if isinstance(fragment, Instance):
			for name, (value, dir) in fragment.named_ports.items():
				self.on_value(value)

		old_local_domains, self._local_domains = self._local_domains, set(self._local_domains)
		for domain_name, domain in fragment.domains.items():
			if domain.local:
				self._local_domains.add(domain_name)
			else:
				self.defined_domains.add(domain_name)

		self.on_statements(fragment.statements)
		for domain_name in fragment.drivers:
			self._add_used_domain(domain_name)
		for subfragment, name in fragment.subfragments:
			self.on_fragment(subfragment)

		self._local_domains = old_local_domains

	def __call__(self, fragment):
		self.on_fragment(fragment)

class DomainRenamer(FragmentTransformer, ValueTransformer, StatementTransformer):
	'''
	Rename domains on given Elaboratable or Module.

	The mapping is provided as a key-value pair to the constructor, where the key is the domain to remap
	and the value is the new domain.

	Parameters
	----------
	**kwargs : str
		Domain translation mapping

	Attention
	---------
	You are not allowed to rename any domain to/from the combinatorial (``comb``) domain.

	Example
	-------
	.. code-block:: py

		m.submodules.timer = timer = DomainRenamer(sync = 'pci')(Timer())

	Raises
	------
	ValueError
		When trying to rename a domain to/from ``comb`` to any other domain.
	'''

	def __init__(self, **kwargs: str) -> None:
		if 'comb' in kwargs.keys():
			raise ValueError(f'The combinatorial domain \'comb\' may not be renamed to \'{kwargs["comb"]}\'')
		if 'comb' in kwargs.values():
			raise ValueError('Domains may not be renamed to the combinatorial domain \'comb\'')

		self.domain_map = OrderedDict(**kwargs)

	def on_ClockSignal(self, value):
		if value.domain in self.domain_map:
			return ClockSignal(self.domain_map[value.domain])
		return value

	def on_ResetSignal(self, value):
		if value.domain in self.domain_map:
			return ResetSignal(
				self.domain_map[value.domain],
				allow_reset_less = value.allow_reset_less
			)
		return value

	def map_domains(self, fragment, new_fragment):
		for domain in fragment.iter_domains():
			cd = fragment.domains[domain]
			if domain in self.domain_map:
				if cd.name == domain:
					# Rename the actual ClockDomain object.
					cd.rename(self.domain_map[domain])
				else:
					if cd.name != self.domain_map[domain]:
						raise ValueError(f'Clock domain mismatch! \'{cd.name}\' != \'{self.domain_map[domain]}\'')
			new_fragment.add_domains(cd)

	def map_drivers(self, fragment, new_fragment):
		for domain, signals in fragment.drivers.items():
			if domain in self.domain_map:
				domain = self.domain_map[domain]
			for signal in signals:
				new_fragment.add_driver(self.on_value(signal), domain)

	def map_memory_ports(self, fragment, new_fragment):
		super().map_memory_ports(fragment, new_fragment)

		for port in new_fragment.read_ports:
			if port.domain in self.domain_map:
				port.domain = self.domain_map[port.domain]

		for port in new_fragment.write_ports:
			if port.domain in self.domain_map:
				port.domain = self.domain_map[port.domain]

class DomainLowerer(FragmentTransformer, ValueTransformer, StatementTransformer):
	def __init__(self, domains = None) -> None:
		self.domains = domains

	def _resolve(self, domain, context):
		if domain not in self.domains:
			raise DomainError(f'Signal {context!r} refers to nonexistent domain \'{domain}\'')
		return self.domains[domain]

	def map_drivers(self, fragment, new_fragment):
		for domain, signal in fragment.iter_drivers():
			new_fragment.add_driver(self.on_value(signal), domain)

	def replace_value_src_loc(self, value, new_value):
		return not isinstance(value, (ClockSignal, ResetSignal))

	def on_ClockSignal(self, value):
		domain = self._resolve(value.domain, value)
		return domain.clk

	def on_ResetSignal(self, value):
		domain = self._resolve(value.domain, value)
		if domain.rst is None:
			if value.allow_reset_less:
				return Const(0)
			else:
				raise DomainError(f'Signal {value!r} refers to reset of reset-less domain \'{value.domain}\'')
		return domain.rst

	def _insert_resets(self, fragment):
		for domain_name, signals in fragment.drivers.items():
			if domain_name is None:
				continue
			domain = fragment.domains[domain_name]
			if domain.rst is None:
				continue
			stmts = [
				signal.eq(Const(signal.reset, signal.width))
				for signal in signals if not signal.reset_less
			]
			fragment.add_statements(Switch(domain.rst, {1: stmts}))

	def on_fragment(self, fragment):
		self.domains = fragment.domains
		new_fragment = super().on_fragment(fragment)
		self._insert_resets(new_fragment)
		return new_fragment

class SampleDomainInjector(ValueTransformer, StatementTransformer):
	def __init__(self, domain) -> None:
		self.domain = domain

	def on_Sample(self, value):
		if value.domain is not None:
			return value
		return Sample(value.value, value.clocks, self.domain)

	def __call__(self, stmts):
		return self.on_statement(stmts)

class SampleLowerer(FragmentTransformer, ValueTransformer, StatementTransformer):
	def __init__(self) -> None:
		self.initial = None
		self.sample_cache = None
		self.sample_stmts = None

	def _name_reset(self, value):
		if isinstance(value, Const):
			return f'c${value.value}', value.value
		elif isinstance(value, Signal):
			return f's${value.name}', value.reset
		elif isinstance(value, ClockSignal):
			return 'clk', 0
		elif isinstance(value, ResetSignal):
			return 'rst', 1
		elif isinstance(value, Initial):
			return 'init', 0 # Past(Initial()) produces 0, 1, 0, 0, ...
		else:
			raise NotImplementedError # :nocov:

	def on_Sample(self, value):
		if value in self.sample_cache:
			return self.sample_cache[value]

		sampled_value = self.on_value(value.value)
		if value.clocks == 0:
			sample = sampled_value
		else:
			if value.domain is None:
				raise ValueError(f'Domain for value \'{value!r}\' is None!')

			sampled_name, sampled_reset = self._name_reset(value.value)
			name = f'$sample${sampled_name}${value.domain}${value.clocks}'
			sample = Signal.like(value.value, name = name, reset_less = True, reset = sampled_reset)
			sample.attrs['torii.sample_reg'] = True

			prev_sample = self.on_Sample(Sample(sampled_value, value.clocks - 1, value.domain))
			if value.domain not in self.sample_stmts:
				self.sample_stmts[value.domain] = []
			self.sample_stmts[value.domain].append(sample.eq(prev_sample))

		self.sample_cache[value] = sample
		return sample

	def on_Initial(self, value):
		if self.initial is None:
			self.initial = Signal(name = 'init')
		return self.initial

	def map_statements(self, fragment, new_fragment):
		self.initial = None
		self.sample_cache = ValueDict()
		self.sample_stmts = OrderedDict()
		new_fragment.add_statements(map(self.on_statement, fragment.statements))
		for domain, stmts in self.sample_stmts.items():
			new_fragment.add_statements(stmts)
			for stmt in stmts:
				new_fragment.add_driver(stmt.lhs, domain)
		if self.initial is not None:
			new_fragment.add_subfragment(Instance('$initstate', o_Y = self.initial))

class SwitchCleaner(StatementVisitor):
	def on_ignore(self, stmt):
		return stmt

	on_Assign = on_ignore
	on_Property = on_ignore

	def on_Switch(self, stmt):
		cases = OrderedDict((k, self.on_statement(s)) for k, s in stmt.cases.items())
		if any(len(s) for s in cases.values()):
			return Switch(stmt.test, cases)

	def on_statements(self, stmts):
		stmts = flatten(self.on_statement(stmt) for stmt in stmts)
		return _StatementList(stmt for stmt in stmts if stmt is not None)

class LHSGroupAnalyzer(StatementVisitor):
	def __init__(self) -> None:
		self.signals = SignalDict()
		self.unions  = OrderedDict()

	def find(self, signal):
		if signal not in self.signals:
			self.signals[signal] = len(self.signals)
		group = self.signals[signal]
		while group in self.unions:
			group = self.unions[group]
		self.signals[signal] = group
		return group

	def unify(self, root, *leaves):
		root_group = self.find(root)
		for leaf in leaves:
			leaf_group = self.find(leaf)
			if root_group == leaf_group:
				continue
			self.unions[leaf_group] = root_group

	def groups(self):
		groups = OrderedDict()
		for signal in self.signals:
			group = self.find(signal)
			if group not in groups:
				groups[group] = SignalSet()
			groups[group].add(signal)
		return groups

	def on_Assign(self, stmt):
		lhs_signals = stmt._lhs_signals()
		if lhs_signals:
			self.unify(*stmt._lhs_signals())

	def on_Property(self, stmt):
		lhs_signals = stmt._lhs_signals()
		if lhs_signals:
			self.unify(*stmt._lhs_signals())

	def on_Switch(self, stmt):
		for case_stmts in stmt.cases.values():
			self.on_statements(case_stmts)

	def on_statements(self, stmts):
		for stmt in stmts:
			self.on_statement(stmt)

	def __call__(self, stmts):
		self.on_statements(stmts)
		return self.groups()

class LHSGroupFilter(SwitchCleaner):
	def __init__(self, signals) -> None:
		self.signals = signals

	def on_Assign(self, stmt):
		# The invariant provided by LHSGroupAnalyzer is that all signals that ever appear together
		# on LHS are a part of the same group, so it is sufficient to check any of them.
		lhs_signals = stmt.lhs._lhs_signals()
		if lhs_signals:
			any_lhs_signal = next(iter(lhs_signals))
			if any_lhs_signal in self.signals:
				return stmt

	def on_Property(self, stmt):
		any_lhs_signal = next(iter(stmt._lhs_signals()))
		if any_lhs_signal in self.signals:
			return stmt

class _ControlInserter(FragmentTransformer):
	def __init__(self, controls) -> None:
		self.src_loc = None
		if isinstance(controls, Value):
			controls = { 'sync': controls }
		self.controls = OrderedDict(controls)

	def on_fragment(self, fragment):
		new_fragment = super().on_fragment(fragment)
		for domain, signals in fragment.drivers.items():
			if domain is None or domain not in self.controls:
				continue
			self._insert_control(new_fragment, domain, signals)
		return new_fragment

	def _insert_control(self, fragment, domain, signals):
		raise NotImplementedError # :nocov:

	def __call__(self, value, *, src_loc_at = 0):
		self.src_loc = tracer.get_src_loc(src_loc_at = src_loc_at)
		return super().__call__(value, src_loc_at = 1 + src_loc_at)

class ResetInserter(_ControlInserter):
	'''
	Inject a synchronous reset signal into the given Elaboratable.
	'''

	def _insert_control(self, fragment, domain, signals):
		stmts = [ s.eq(Const(s.reset, s.width)) for s in signals if not s.reset_less ]
		fragment.add_statements(Switch(self.controls[domain], { 1: stmts }, src_loc = self.src_loc))

class EnableInserter(_ControlInserter):
	'''
	Inject a synchronous enable signal into the given Elaboratable.
	'''

	def _insert_control(self, fragment, domain, signals):
		stmts = [s.eq(s) for s in signals]
		fragment.add_statements(Switch(self.controls[domain], { 0: stmts }, src_loc = self.src_loc))

	def on_fragment(self, fragment):
		new_fragment = super().on_fragment(fragment)
		if isinstance(new_fragment, MemoryInstance):
			for port in new_fragment.read_ports:
				if port.domain in self.controls:
					port.en = port.en & self.controls[port.domain]
			for port in new_fragment.write_ports:
				if port.domain in self.controls:
					port.en = Mux(self.controls[port.domain], port.en, Const(0, len(port.en)))

		return new_fragment
