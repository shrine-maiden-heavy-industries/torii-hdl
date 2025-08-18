# SPDX-License-Identifier: BSD-2-Clause

from contextlib  import contextmanager
from wasmtime    import Store, Module, Instance, Func, FuncType, ValType

from ...hdl.ast  import SignalSet
from ...hdl.ir   import Fragment
from ...hdl.xfrm import LHSGroupFilter, StatementVisitor, ValueVisitor
from .._base     import BaseProcess

__all__ = (
	'WASMRTLProcess',
	'_WASMExec',
	'_WASMFragmentCompiler',
)

class WASMRTLProcess(BaseProcess):
	__slots__ = ('is_comb', 'runnable', 'passive', 'run')

	def __init__(self, *, is_comb) -> None:
		self.is_comb  = is_comb

		self.reset()

	def reset(self):
		self.runnable = self.is_comb
		self.passive  = True

class _WASMExec:
	__slots__ = ('func', 'store')

	def __init__(self, func: Func, store: Store) -> None:
		self.func = func
		self.store = store

	def __call__(self) -> None:
		self.func(self.store)

class _WASMEmitter:
	def __init__(self):
		self._level = 0
		self._suffix = 0
		self._imports = []
		self._globals = []
		self._variables = []
		self._instructions = []

	def append(self, code):
		self._instructions.append('\t\t' + '\t' * self._level)
		self._instructions.append(code)
		self._instructions.append('\n')

	def add_func(self, name):
		self._imports.append('\t')
		self._imports.append(f'(func ${name} (import "" "{name}") (param i64))')
		self._imports.append('\n')

	def add_global_var(self, name):
		self._globals.append('\t')
		self._globals.append(f'(global ${name} (import "" "{name}") (mut i64))')
		self._globals.append('\n')

	def add_variable(self, name):
		self._variables.append('\t\t')
		self._variables.append(f'(local ${name} i64)')
		self._variables.append('\n')

	def def_var(self, name, code):
		name = f'{name}_{self._suffix}'
		self._suffix += 1
		self.add_variable(name)
		self.append(f'(local.set ${name} {code})')
		return name

	@contextmanager
	def indent(self):
		self._level += 1
		yield
		self._level -= 1

	def flush(self, result: bool = False):
		module = '(module\n'
		module += ''.join(self._globals)
		module += '\n'
		module += ''.join(self._imports)
		module += '\n'
		if result:
			module += '\t(func (export "run") (result i64)\n'
		else:
			module += '\t(func (export "run")\n'
		module += ''.join(self._variables)
		module += ''.join(self._instructions)
		module += "\n\t)\n)\n"

		self._instructions.clear()
		return module


class _Compiler:
	def __init__(self, state, emitter) -> None:
		self.state = state
		self.emitter = emitter

class _ValueCompiler(ValueVisitor, _Compiler):
	def on_value(self, value):
		# Very large values are unlikely to compile or simulate in reasonable time.
		# probably not neeeded on wasm?
		if len(value) > 2 ** 16:
			if value.src_loc:
				src = '{}:{}'.format(*value.src_loc)
			else:
				src = 'unknown location'
			raise OverflowError(
				f'Value defined at {src} is {len(value)} bits wide, which is unlikely to simulate '
				'in reasonable time'
			)

		val = super().on_value(value)
		if isinstance(val, str) and len(val) > 1000:
			return self.emitter.def_var('intermediate', val)
		return val

	def on_ClockSignal(self, value):
		raise NotImplementedError # :nocov:

	def on_ResetSignal(self, value):
		raise NotImplementedError # :nocov:

	def on_AnyValue(self, value):
		raise NotImplementedError # :nocov:

	def on_Sample(self, value):
		raise NotImplementedError # :nocov:

	def on_Initial(self, value):
		raise NotImplementedError # :nocov:

class _RHSValueCompiler(_ValueCompiler):
	def __init__(self, state, emitter, *, mode, inputs = None) -> None:
		super().__init__(state, emitter)
		if mode not in ('curr', 'next'):
			raise ValueError(f'Expected mode to be \'curr\', or \'next\', not \'{mode!r}\'')
		self.mode = mode
		# If not None, `inputs` gets populated with RHS signals.
		self.inputs = inputs

	def on_Const(self, value):
		return f'(i64.const {value.value})'

	def on_Signal(self, value):
		if self.inputs is not None:
			self.inputs.add(value)

		if self.mode == 'curr':
			return f'(global.get $slots_{self.state.get_signal(value)}_{self.mode})'
		else:
			return f'(local.get $next_{self.state.get_signal(value)})'

	def on_Operator(self, value):
		def mask(value):
			value_mask = (1 << len(value)) - 1
			return f'(i64.and (i64.const {value_mask:#x}) {self(value)})'

		def sign(value):
			if value.shape().signed:
				raise NotImplementedError
			else: # unsigned
				return mask(value)

		if len(value.operands) == 2:
			lhs, rhs = value.operands
			if value.operator == '+':
				return f'(i64.add {sign(lhs)} {sign(rhs)})'
			if value.operator == '&':
				return f'(i64.and {sign(lhs)} {sign(rhs)})'
			if value.operator == '==':
				# i64.eq will push i32 into a stack so we need to extend it to i64
				return f'(i64.extend_i32_u (i64.eq {sign(lhs)} {sign(rhs)}))'
		raise NotImplementedError(f'Operator \'{value.operator}\' not implemented') # :nocov:

	def on_Slice(self, value):
		raise NotImplementedError

	def on_Part(self, value):
		raise NotImplementedError

	def on_Cat(self, value):
		gen_parts = []
		offset = 0
		for part in value.parts:
			part_mask = (1 << len(part)) - 1
			gen_parts.append(f'(i64.shl (i64.and (i64.const {part_mask:#x}) {self(part)}) (i64.const {offset}))')
			offset += len(part)
		if gen_parts:
			return f'{"".join(gen_parts)}'
		return '0'

	def on_ArrayProxy(self, value):
		raise NotImplementedError

	@classmethod
	def compile(cls, state, value, *, mode):
		emitter = _WASMEmitter()
		compiler = cls(state, emitter, mode = mode)
		emitter.append(compiler(value))

		# TODO: only import signals that are actually needed. They need to be in order!
		for slot in state.slots:
			signal_index = state.get_signal(slot.signal)
			emitter.add_global_var(f'slots_{signal_index}_curr')
			emitter.add_global_var(f'slots_{signal_index}_next')
			emitter.add_func(f'slots_{signal_index}_set')

		output_code = emitter.flush(True)
		return output_code

class _LHSValueCompiler(_ValueCompiler):
	def __init__(self, state, emitter, *, rhs, outputs = None) -> None:
		super().__init__(state, emitter)
		# `rrhs` is used to translate rvalues that are syntactically a part of an lvalue, e.g.
		# the offset of a Part.
		self.rrhs = rhs
		# `lrhs` is used to translate the read part of a read-modify-write cycle during partial
		# update of an lvalue.
		self.lrhs = _RHSValueCompiler(state, emitter, mode = 'next', inputs = None)
		# If not None, `outputs` gets populated with signals on LHS.
		self.outputs = outputs

	def on_Const(self, value):
		raise TypeError # :nocov:

	def on_Signal(self, value):
		if self.outputs is not None:
			self.outputs.add(value)

		def gen(arg):
			value_mask = (1 << len(value)) - 1
			if value.shape().signed:
				raise NotImplementedError
			else: # unsigned
				value_sign = f'(i64.and (i64.const {value_mask:#x}) {arg})'
			self.emitter.append(f'(local.set $next_{self.state.get_signal(value)} {value_sign})')
		return gen

	def on_Operator(self, value):
		raise NotImplementedError

	def on_Slice(self, value):
		raise NotImplementedError

	def on_Part(self, value):
		raise NotImplementedError

	def on_Cat(self, value):
		raise NotImplementedError

	def on_ArrayProxy(self, value):
		raise NotImplementedError

class _StatementCompiler(StatementVisitor, _Compiler):
	def __init__(self, state, emitter, *, inputs = None, outputs = None) -> None:
		super().__init__(state, emitter)
		self.rhs = _RHSValueCompiler(state, emitter, mode = 'curr', inputs = inputs)
		self.lhs = _LHSValueCompiler(state, emitter, rhs = self.rhs, outputs = outputs)

	def on_statements(self, stmts):
		for stmt in stmts:
			self(stmt)
		if not stmts:
			raise NotImplementedError

	def on_Assign(self, stmt):
		gen_rhs_value = self.rhs(stmt.rhs) # check for oversized value before generating mask
		gen_rhs = f'(i64.and (i64.const {(1 << len(stmt.rhs)) - 1:#x}) {gen_rhs_value})'
		if stmt.rhs.shape().signed:
			raise NotImplementedError
		return self.lhs(stmt.lhs)(gen_rhs)

	def on_Switch(self, stmt):
		gen_test_value = self.rhs(stmt.test) # check for oversized value before generating mask
		gen_test = self.emitter.def_var('test', f'(i64.and (i64.const {(1 << len(stmt.test)) - 1:#x}) {gen_test_value})')

		for index, (patterns, stmts) in enumerate(stmt.cases.items()):
			gen_checks = []
			if not patterns:
				gen_checks.append('(i32.eq (i32.const 1) (i32.const 1))')
			else:
				for pattern in patterns:
					if "-" in pattern:
						mask  = int(''.join('0' if b == '-' else '1' for b in pattern), 2)
						value = int(''.join('0' if b == '-' else b for b in pattern), 2)
						gen_checks.append(f'{value} == ({mask} & {gen_test})')
					else:
						value = int(pattern or '0', 2)
						gen_checks.append(f'(i64.eq (i64.const {value}) (local.get ${gen_test}))')

			# TODO: or statements
			if index == 0:
				self.emitter.append(f'(if {"".join(gen_checks)} (then')
			else:
				self.emitter.append(f'(else (if {"".join(gen_checks)} (then')

			with self.emitter.indent():
				self(stmts)

			self.emitter.append(')')

		# Close down all the nested if-elses
		if len(stmt.cases.items()) > 0:
			self.emitter.append(')' + '))' * (len(stmt.cases.items()) - 1))

	def on_Property(self, stmt):
		raise NotImplementedError # :nocov:

	@classmethod
	def compile(cls, state, stmt):
		output_indexes = [state.get_signal(signal) for signal in stmt._lhs_signals()]
		emitter = _WASMEmitter()
		for signal_index in output_indexes:
			emitter.add_variable(f'next_{signal_index}')
			emitter.append(f'(local.set $next_{signal_index} (global.get $slots_{signal_index}_next))')
		compiler = cls(state, emitter)
		compiler(stmt)
		for signal_index in output_indexes:
			emitter.append(f'(call $slots_{signal_index}_set (local.get $next_{signal_index}))')

		# TODO: only import signals that are actually needed. They need to be in order!
		for slot in state.slots:
			signal_index = state.get_signal(slot.signal)
			emitter.add_global_var(f'slots_{signal_index}_curr')
			emitter.add_global_var(f'slots_{signal_index}_next')
			emitter.add_func(f'slots_{signal_index}_set')

		output_code = emitter.flush()
		return output_code

class _WASMFragmentCompiler:
	def __init__(self, state) -> None:
		self.state = state

	def __call__(self, fragment: Fragment):
		processes = set()

		for domain_name, domain_signals in fragment.drivers.items():
			domain_stmts = LHSGroupFilter(domain_signals)(fragment.statements)
			domain_process = WASMRTLProcess(is_comb = domain_name is None)

			emitter = _WASMEmitter()
			if domain_name is None:
				for signal in domain_signals:
					signal_index = self.state.get_signal(signal)
					emitter.add_variable(f'next_{signal_index}')
					emitter.append(f'(local.set $next_{signal_index} (i64.const {signal.reset}))')

				inputs = SignalSet()
				_StatementCompiler(self.state, emitter, inputs = inputs)(domain_stmts)

				for input in inputs:
					self.state.add_trigger(domain_process, input)

			else:
				domain = fragment.domains[domain_name]
				clk_trigger = 1 if domain.clk_edge == 'pos' else 0
				self.state.add_trigger(domain_process, domain.clk, trigger = clk_trigger)
				if domain.rst is not None and domain.async_reset:
					rst_trigger = 1
					self.state.add_trigger(domain_process, domain.rst, trigger = rst_trigger)

				for signal in domain_signals:
					signal_index = self.state.get_signal(signal)
					emitter.add_variable(f'next_{signal_index}')
					emitter.append(f'(local.set $next_{signal_index} (global.get $slots_{signal_index}_next))')

				_StatementCompiler(self.state, emitter)(domain_stmts)

			for signal in domain_signals:
				signal_index = self.state.get_signal(signal)
				emitter.append(f'(call $slots_{signal_index}_set (local.get $next_{signal_index}))')

			glob_vars = []
			glob_func = []

			for slot in self.state.slots:
				signal_index = self.state.get_signal(slot.signal)
				emitter.add_global_var(f'slots_{signal_index}_curr')
				emitter.add_global_var(f'slots_{signal_index}_next')
				emitter.add_func(f'slots_{signal_index}_set')
				glob_func.append(Func(self.state.store, FuncType([ValType.i64()], []), slot.set))
				# current is first, next is second
				glob_vars.append(slot.curr.wasm_value())
				glob_vars.append(slot.next.wasm_value())

			# Make sure that globals are imported in the order they are imported
			# in the WASMEmitter
			glob_vars.extend(glob_func)
			module_code = emitter.flush()
			module = Module(self.state.store.engine, module_code)
			instance = Instance(self.state.store, module, glob_vars)
			run = instance.exports(self.state.store)["run"]
			domain_process.run = _WASMExec(run, self.state.store)
			processes.add(domain_process)

		return processes
