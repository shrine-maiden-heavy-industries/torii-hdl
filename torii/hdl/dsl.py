# SPDX-License-Identifier: BSD-2-Clause

import warnings
from collections     import OrderedDict
from collections.abc import Callable, Iterable, Generator
from contextlib      import _GeneratorContextManager, contextmanager
from functools       import wraps
from sys             import version_info
from typing          import ParamSpec, Any, TypedDict, TYPE_CHECKING

from ..util          import flatten, tracer
from ..util.units    import bits_for
from .ast            import (
	Assign, Cat, Const, Operator, Property, Signal, SignalDict, Statement, Switch, Value,
	_StatementList, ValueCastT
)
from .cd             import ClockDomain
from .ir             import Elaboratable, Fragment
from .xfrm           import SampleDomainInjector
from .._typing       import SrcLoc, SwitchCaseT

if TYPE_CHECKING:
	from ..build.plat import Platform

__all__ = (
	'Module',
	'SyntaxError',
	'SyntaxWarning',
)


class SyntaxError(Exception):
	pass


class SyntaxWarning(Warning):
	pass


class _ModuleBuilderProxy:
	_builder: 'Module'
	_depth: int

	def __init__(self, builder: 'Module', depth: int):
		object.__setattr__(self, '_builder', builder)
		object.__setattr__(self, '_depth', depth)


class _ModuleBuilderDomain(_ModuleBuilderProxy):
	def __init__(self, builder: 'Module', depth: int, domain: str | None):
		super().__init__(builder, depth)
		self._domain = domain

	def __iadd__(self, assigns):
		self._builder._add_statement(assigns, domain = self._domain, depth = self._depth)
		return self


class _ModuleBuilderDomains(_ModuleBuilderProxy):
	def __getattr__(self, name: str):
		if name == 'submodules':
			warnings.warn(
				f'Using \'<module>.d.{name}\' would add statements to clock domain {name!r}; '
				f'did you mean <module>.{name} instead?',
				SyntaxWarning, stacklevel = 2
			)
		if name == 'comb':
			domain = None
		else:
			domain = name
		return _ModuleBuilderDomain(self._builder, self._depth, domain)

	def __getitem__(self, name):
		return self.__getattr__(name)

	def __setattr__(self, name, value):
		if name == '_depth':
			object.__setattr__(self, name, value)
		elif not isinstance(value, _ModuleBuilderDomain):
			raise AttributeError(f'Cannot assign \'d.{name}\' attribute; did you mean \'d.{name} +=\'?')

	def __setitem__(self, name, value):
		return self.__setattr__(name, value)


class _ModuleBuilderRoot:
	def __init__(self, builder: 'Module', depth: int):
		self._builder = builder
		self.domain = self.d = _ModuleBuilderDomains(builder, depth)

	def __getattr__(self, name):
		if name in ('comb', 'sync'):
			raise AttributeError(f'\'{type(self).__name__}\' object has no attribute \'{name}\'; did you mean \'d.{name}\'?')
		raise AttributeError(f'\'{type(self).__name__}\' object has no attribute \'{name}\'')


class _ModuleBuilderSubmodules:
	_builder: 'Module'

	def __init__(self, builder: 'Module'):
		object.__setattr__(self, '_builder', builder)

	def __iadd__(self, modules):
		for module in flatten([modules]):
			self._builder._add_submodule(module)
		return self

	def __setattr__(self, name, submodule):
		self._builder._add_submodule(submodule, name)

	def __setitem__(self, name, value):
		return self.__setattr__(name, value)

	def __getattr__(self, name):
		return self._builder._get_submodule(name)

	def __getitem__(self, name):
		return self.__getattr__(name)


class _ModuleBuilderDomainSet:
	_builder: 'Module'

	def __init__(self, builder: 'Module'):
		object.__setattr__(self, '_builder', builder)

	def __iadd__(self, domains: Iterable):
		for domain in flatten([domains]):
			if not isinstance(domain, ClockDomain):
				raise TypeError(f'Only clock domains may be added to `m.domains`, not {domain!r}')
			self._builder._add_domain(domain)
		return self

	def __setattr__(self, name, domain):
		if not isinstance(domain, ClockDomain):
			raise TypeError(f'Only clock domains may be added to `m.domains`, not {domain!r}')
		if domain.name != name:
			raise NameError(f'Clock domain name {domain.name!r} must match name in `m.domains.{name} += ...` syntax')
		self._builder._add_domain(domain)

Params = ParamSpec('Params')

# It's not particularly clean to depend on an internal interface, but, unfortunately, __bool__
# must be defined on a class to be called during implicit conversion.
class _GuardedContextManager(_GeneratorContextManager):
	def __init__(self, keyword: str, func: Callable[Params, Generator[Any, Any, None]], args: tuple, kwds: dict):
		self.keyword = keyword
		return super().__init__(func, args, kwds)

	def __bool__(self):
		raise SyntaxError(f'`if m.{self.keyword}(...):` does not work; use `with m.{self.keyword}(...)`')

def _guardedcontextmanager(keyword: str):
	def decorator(func: Callable[Params, Generator[Any, Any, None]]) -> Callable[Params, _GeneratorContextManager]:
		@wraps(func)
		def helper(*args: Params.args, **kwds: Params.kwargs):
			return _GuardedContextManager(keyword, func, args, kwds)
		return helper
	return decorator

class FSM:
	def __init__(self, state, encoding, decoding):
		self.state    = state
		self.encoding = encoding
		self.decoding = decoding

	def ongoing(self, name):
		if name not in self.encoding:
			self.encoding[name] = len(self.encoding)
		return Operator('==', [ self.state, self.encoding[name] ], src_loc_at = 0)

class _IfDict(TypedDict):
	depth: int
	tests: list
	bodies: list
	src_loc: SrcLoc
	src_locs: list[SrcLoc]

class _SwitchDict(TypedDict):
	test: Value
	cases: OrderedDict[SwitchCaseT, _StatementList]
	src_loc: SrcLoc
	case_src_locs: dict[SwitchCaseT, SrcLoc]

class _FSMDict(TypedDict):
	name: str
	signal: Signal
	reset: str | None
	domain: str
	encoding: OrderedDict[str, int]
	decoding: OrderedDict
	states: OrderedDict[str, _StatementList]
	src_loc: SrcLoc
	state_src_locs: dict[str, SrcLoc]

_CtrlEntry = _IfDict | _SwitchDict | _FSMDict

class Module(_ModuleBuilderRoot, Elaboratable):
	@classmethod
	def __init_subclass__(cls):
		raise SyntaxError(
			'Instead of inheriting from `Module`, inherit from `Elaboratable` '
			'and return a `Module` from the `elaborate(self, platform)` method'
		)

	def __init__(self):
		super().__init__(builder = self, depth = 0)
		self.submodules    = _ModuleBuilderSubmodules(self)
		self.domains       = _ModuleBuilderDomainSet(self)

		self._statements   = Statement.cast([])
		self._ctrl_context = None
		self._ctrl_stack : list[tuple[str, _CtrlEntry]]  = []

		self._driving      = SignalDict[str]()
		self._named_submodules = {}
		self._anon_submodules  = []
		self._domains      = {}
		self._generated    = {}

	def _check_context(self, construct, context):
		if self._ctrl_context != context:
			if self._ctrl_context is None:
				raise SyntaxError(f'{construct} is not permitted outside of {context}')
			else:
				if self._ctrl_context == 'Switch':
					secondary_context = 'Case'
				if self._ctrl_context == 'FSM':
					secondary_context = 'State'
				raise SyntaxError(
					f'{construct} is not permitted directly inside of {self._ctrl_context}; '
					f'it is permitted inside of {self._ctrl_context} {secondary_context}'
				)

	def _get_ctrl(self, name: str):
		if self._ctrl_stack:
			top_name, top_data = self._ctrl_stack[-1]
			if top_name == name:
				return top_data

	def _flush_ctrl(self):
		while len(self._ctrl_stack) > self.domain._depth:
			self._pop_ctrl()

	def _set_ctrl(self, name: str, data: _CtrlEntry):
		self._flush_ctrl()
		self._ctrl_stack.append((name, data))
		return data

	def _check_signed_cond(self, cond: ValueCastT):
		cond = Value.cast(cond)
		if version_info < (3, 12, 0) and cond.shape().signed:
			# TODO(py3.11): remove; ~True is a warning in 3.12+, finally!
			warnings.warn(
				'Signed values in If/Elif conditions usually result from inverting '
				'Python booleans with ~, which leads to unexpected results. '
				'Replace `~flag` with `not flag`. (If this is a false positive, '
				'silence this warning with `m.If(x)` → `m.If(x.bool())`.)',
				SyntaxWarning, stacklevel = 4
			)
		return cond

	@_guardedcontextmanager('If')
	def If(self, cond: ValueCastT):
		self._check_context('If', context = None)
		cond = self._check_signed_cond(cond)
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		if_data = self._set_ctrl('If', {
			'depth'   : self.domain._depth,
			'tests'   : [],
			'bodies'  : [],
			'src_loc' : src_loc,
			'src_locs': [],
		})
		if TYPE_CHECKING:
			assert isinstance(if_data, _IfDict)
		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self.domain._depth += 1
			yield
			self._flush_ctrl()
			if_data['tests'].append(cond)
			if_data['bodies'].append(self._statements)
			if_data['src_locs'].append(src_loc)
		finally:
			self.domain._depth -= 1
			self._statements = _outer_case

	@_guardedcontextmanager('Elif')
	def Elif(self, cond: ValueCastT):
		self._check_context('Elif', context = None)
		cond = self._check_signed_cond(cond)
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		if_data = self._get_ctrl('If')
		if TYPE_CHECKING:
			assert if_data is None or isinstance(if_data, _IfDict)
		if if_data is None or if_data['depth'] != self.domain._depth:
			raise SyntaxError('Elif without preceding If')
		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self.domain._depth += 1
			yield
			self._flush_ctrl()
			if_data['tests'].append(cond)
			if_data['bodies'].append(self._statements)
			if_data['src_locs'].append(src_loc)
		finally:
			self.domain._depth -= 1
			self._statements = _outer_case

	@_guardedcontextmanager('Else')
	def Else(self):
		self._check_context('Else', context = None)
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		if_data = self._get_ctrl('If')
		if TYPE_CHECKING:
			assert if_data is None or isinstance(if_data, _IfDict)
		if if_data is None or if_data['depth'] != self.domain._depth:
			raise SyntaxError('Else without preceding If/Elif')
		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self.domain._depth += 1
			yield
			self._flush_ctrl()
			if_data['bodies'].append(self._statements)
			if_data['src_locs'].append(src_loc)
		finally:
			self.domain._depth -= 1
			self._statements = _outer_case
		self._pop_ctrl()

	@contextmanager
	def Switch(self, test):
		self._check_context('Switch', context = None)
		self._set_ctrl('Switch', {
			'test'         : Value.cast(test),
			'cases'        : OrderedDict(),
			'src_loc'      : tracer.get_src_loc(src_loc_at = 1),
			'case_src_locs': {},
		})
		try:
			self._ctrl_context = 'Switch'
			self.domain._depth += 1
			yield
		finally:
			self.domain._depth -= 1
			self._ctrl_context = None
		self._pop_ctrl()

	@contextmanager
	def Case(self, *patterns):
		if not patterns:
			raise ValueError('Empty Case() clauses have been superseded by Default()')

		self._check_context('Case', context = 'Switch')
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		switch_data = self._get_ctrl('Switch')
		if TYPE_CHECKING:
			assert switch_data is None or isinstance(switch_data, _SwitchDict)
		if switch_data is None:
			raise SyntaxError('Case outside of Switch block')
		new_patterns: _PatternTuple = ()
		if () in switch_data['cases']:
			warnings.warn(
				'Case statements are order-dependant, any Case after a Default will be ignored',
				SyntaxWarning, stacklevel = 3
			)

		# This code should accept exactly the same patterns as `v.matches(...)`.
		for pattern in patterns:
			if isinstance(pattern, str) and any(bit not in '01- \t' for bit in pattern):
				raise SyntaxError(
					f'Case pattern \'{pattern}\' must consist of 0, 1, and - (don\'t care) bits, and may '
					'include whitespace'
				)
			if (isinstance(pattern, str) and
					len("".join(pattern.split())) != len(switch_data['test'])):
				raise SyntaxError(
					f'Case pattern \'{pattern}\' must have the same width as switch value '
					f'(which is {len(switch_data["test"])})'
				)
			if isinstance(pattern, str):
				new_patterns = (*new_patterns, pattern)
			else:
				orig_pattern = pattern
				try:
					pattern = Const.cast(pattern)
				except TypeError as error:
					raise SyntaxError(
						'Case pattern must be a string or a const-castable expression, '
						f'not {pattern!r}'
					) from error

				pattern_len = bits_for(pattern.value)
				if pattern.value == 0:
					pattern_len = 0
				if pattern_len > len(switch_data['test']):
					warnings.warn(
						f'Case pattern \'{orig_pattern!r}\' ({pattern_len}\'{pattern.value:b}) is wider than '
						f'switch value (which has width {len(switch_data["test"])}); comparison will never be true',
						SyntaxWarning, stacklevel = 2
					)
					continue
				new_patterns = (*new_patterns, pattern.value)
		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self._ctrl_context = None
			yield
			self._flush_ctrl()
			# If none of the provided cases can possibly be true, omit this branch completely.
			# This needs to be differentiated from no cases being provided in the first place,
			# which means the branch will always match.
			# Likewise, omit this branch if another branch with this exact set of patterns already
			# exists (since otherwise we'd overwrite the previous branch's slot in the dict).
			if not (patterns and not new_patterns) and new_patterns not in switch_data['cases']:
				switch_data['cases'][new_patterns] = self._statements
				switch_data['case_src_locs'][new_patterns] = src_loc
		finally:
			self._ctrl_context = 'Switch'
			self._statements = _outer_case

	@contextmanager
	def Default(self):
		self._check_context('Default', context = 'Switch')
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		switch_data = self._get_ctrl('Switch')
		if () in switch_data['cases']:
			raise SyntaxError(
				'Multiple Default statements within a switch are not allowed, '
				'as only the first Default will ever be considered.',
			)

		if TYPE_CHECKING:
			assert switch_data is None or isinstance(switch_data, _SwitchDict)
		if switch_data is None:
			raise SyntaxError('Default outside of Switch block')

		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self._ctrl_context = None
			yield
			self._flush_ctrl()
			if () not in switch_data['cases']:
				switch_data['cases'][()] = self._statements
				switch_data['case_src_locs'][()] = src_loc
		finally:
			self._ctrl_context = 'Switch'
			self._statements = _outer_case

	@contextmanager
	def FSM(self, reset: str | None = None, domain = 'sync', name = 'fsm'):
		self._check_context('FSM', context = None)
		if domain == 'comb':
			raise ValueError(f'FSM may not be driven by the \'{domain}\' domain')
		fsm_data = self._set_ctrl('FSM', {
			'name'          : name,
			'signal'        : Signal(name = f'{name}_state', src_loc_at = 2),
			'reset'         : reset,
			'domain'        : domain,
			'encoding'      : OrderedDict(),
			'decoding'      : OrderedDict(),
			'states'        : OrderedDict(),
			'src_loc'       : tracer.get_src_loc(src_loc_at = 1),
			'state_src_locs': {},
		})
		if TYPE_CHECKING:
			assert isinstance(fsm_data, _FSMDict)
		self._generated[name] = fsm = FSM(
			fsm_data['signal'], fsm_data['encoding'], fsm_data['decoding']
		)
		try:
			self._ctrl_context = 'FSM'
			self.domain._depth += 1
			yield fsm
			for state_name in fsm_data['encoding']:
				if state_name not in fsm_data['states']:
					raise NameError(f'FSM state \'{state_name}\' is referenced but not defined')
		finally:
			self.domain._depth -= 1
			self._ctrl_context = None
		self._pop_ctrl()

	@contextmanager
	def State(self, name: str):
		self._check_context('FSM State', context = 'FSM')
		src_loc = tracer.get_src_loc(src_loc_at = 1)
		fsm_data = self._get_ctrl('FSM')
		if TYPE_CHECKING:
			assert fsm_data is None or isinstance(fsm_data, _FSMDict)
		if fsm_data is None:
			raise SyntaxError('State outside of FSM block')
		if name in fsm_data['states']:
			raise NameError(f'FSM state \'{name}\' is already defined')
		if name not in fsm_data['encoding']:
			fsm_data['encoding'][name] = len(fsm_data['encoding'])
		_outer_case = self._statements
		try:
			self._statements = Statement.cast([])
			self._ctrl_context = None
			yield
			self._flush_ctrl()
			fsm_data['states'][name] = self._statements
			fsm_data['state_src_locs'][name] = src_loc
		finally:
			self._ctrl_context = 'FSM'
			self._statements = _outer_case

	@property
	def next(self):
		raise SyntaxError('Only assignment to `m.next` is permitted')

	@next.setter
	def next(self, name):
		if self._ctrl_context != 'FSM':
			for level, (ctrl_name, ctrl_data) in enumerate(reversed(self._ctrl_stack)):
				if ctrl_name == 'FSM':
					if TYPE_CHECKING:
						assert isinstance(ctrl_data, _FSMDict)
					if name not in ctrl_data['encoding']:
						ctrl_data['encoding'][name] = len(ctrl_data['encoding'])
					self._add_statement(
						assigns = [ ctrl_data['signal'].eq(ctrl_data['encoding'][name]) ],
						domain  = ctrl_data['domain'],
						depth   = len(self._ctrl_stack)
					)
					return

		raise SyntaxError('`m.next = <...>` is only permitted inside an FSM state')

	def _pop_ctrl(self):
		name, data = self._ctrl_stack.pop()
		src_loc = data['src_loc']

		if name == 'If':
			if TYPE_CHECKING:
				assert isinstance(data, _IfDict)
			if_tests, if_bodies = data['tests'], data['bodies']
			if_src_locs = data['src_locs']

			tests, cases = [], OrderedDict()
			for if_test, if_case in zip(if_tests + [ None ], if_bodies):
				if if_test is not None:
					if len(if_test) != 1:
						if_test = if_test.bool()
					tests.append(if_test)

				if if_test is not None:
					match = ('1' + '-' * (len(tests) - 1)).rjust(len(if_tests), '-')
				else:
					match = None
				cases[match] = if_case

			self._statements.append(Switch(Cat(tests), cases,
				src_loc = src_loc, case_src_locs = dict(zip(cases, if_src_locs))))

		if name == 'Switch':
			if TYPE_CHECKING:
				assert isinstance(data, _SwitchDict)
			switch_test, switch_cases = data['test'], data['cases']
			switch_case_src_locs = data['case_src_locs']

			self._statements.append(
				Switch(
					switch_test,
					switch_cases,
					src_loc = src_loc,
					case_src_locs = switch_case_src_locs
				)
			)

		if name == 'FSM':
			if TYPE_CHECKING:
				assert isinstance(data, _FSMDict)
			fsm_signal = data['signal']
			fsm_reset = data['reset']
			fsm_encoding = data['encoding']
			fsm_decoding = data['decoding']
			fsm_states = data['states']
			fsm_state_src_locs = data['state_src_locs']
			if not fsm_states:
				return
			fsm_signal.width = bits_for(len(fsm_encoding) - 1)
			if fsm_reset is None:
				fsm_signal.reset = fsm_encoding[next(iter(fsm_states))]
			else:
				fsm_signal.reset = fsm_encoding[fsm_reset]
			# The FSM is encoded such that the state with encoding 0 is always the reset state.
			fsm_decoding.update((n, s) for s, n in fsm_encoding.items())
			fsm_signal.decoder = lambda n: "{}/{}".format(fsm_decoding[n], n)
			self._statements.append(
				Switch(
					fsm_signal,
					OrderedDict((fsm_encoding[name], stmts) for name, stmts in fsm_states.items()),
					src_loc = src_loc,
					case_src_locs = {
						fsm_encoding[name]: fsm_state_src_locs[name]
						for name in fsm_states
					}
				)
			)

	def _add_statement(self, assigns, domain: str, depth, compat_mode = False):
		def domain_name(domain):
			if domain is None:
				return 'comb'
			else:
				return domain

		while len(self._ctrl_stack) > self.domain._depth:
			self._pop_ctrl()

		for stmt in Statement.cast(assigns):
			if not compat_mode and not isinstance(stmt, (Assign, Property)):
				raise SyntaxError(f'Only assignments and property checks may be appended to d.{domain_name(domain)}')

			stmt._MustUse__used = True
			stmt = SampleDomainInjector(domain)(stmt)

			for signal in stmt._lhs_signals():
				if signal not in self._driving:
					self._driving[signal] = domain
				elif self._driving[signal] != domain:
					cd_curr = self._driving[signal]
					raise SyntaxError(
						f'Driver-driver conflict: trying to drive {signal!r} from d.{domain_name(domain)}, but it is '
						f'already driven from d.{domain_name(cd_curr)}')

			self._statements.append(stmt)

	def _add_submodule(self, submodule, name = None):
		if not hasattr(submodule, 'elaborate'):
			raise TypeError(f'Trying to add {submodule!r}, which does not implement .elaborate(), as a submodule')
		if name is None:
			self._anon_submodules.append(submodule)
		else:
			if name in self._named_submodules:
				raise NameError(f'Submodule named \'{name}\' already exists')
			self._named_submodules[name] = submodule

	def _get_submodule(self, name: str):
		if name in self._named_submodules:
			return self._named_submodules[name]
		else:
			raise AttributeError(f'No submodule named \'{name}\' exists')

	def _add_domain(self, cd: ClockDomain):
		if cd.name in self._domains:
			raise NameError(f'Clock domain named \'{cd.name}\' already exists')
		self._domains[cd.name] = cd

	def _flush(self):
		while self._ctrl_stack:
			self._pop_ctrl()

	def elaborate(self, platform: 'Platform | None'):
		self._flush()

		fragment = Fragment()
		for name in self._named_submodules:
			fragment.add_subfragment(Fragment.get(self._named_submodules[name], platform), name)
		for submodule in self._anon_submodules:
			fragment.add_subfragment(Fragment.get(submodule, platform), None)
		statements = SampleDomainInjector('sync')(self._statements)
		fragment.add_statements(statements)
		for signal, domain in self._driving.items():
			fragment.add_driver(signal, domain)
		fragment.add_domains(self._domains.values())
		fragment.generated.update(self._generated)
		return fragment
