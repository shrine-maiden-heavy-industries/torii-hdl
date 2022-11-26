# SPDX-License-Identifier: BSD-2-Clause

from collections  import OrderedDict
from abc          import ABCMeta, abstractmethod
from typing       import (
	Union, Iterable, IO, Optional, Dict, Tuple,
	Type, Generator, TypeVar, Literal, List
)
import os
import textwrap
import re
import jinja2

from ..            import __version__
from .._toolchain  import *
from ..hdl         import *
from ..hdl.xfrm    import SampleLowerer, DomainLowerer
from ..lib.io      import Pin
from ..lib.cdc     import ResetSynchronizer
from ..back        import rtlil, verilog
from ..util.string import ascii_escape, tcl_escape, tcl_quote
from .dsl          import Clock, Attrs
from .res          import *
from .run          import *

__all__ = (
	'Platform',
	'TemplatedPlatform',
)


class Platform(ResourceManager, metaclass = ABCMeta):
	@property
	@abstractmethod
	def resources(self):
		raise NotImplementedError('Platform must implement this property')

	@property
	@abstractmethod
	def connectors(self):
		raise NotImplementedError('Platform must implement this property')

	default_clk    = None
	default_rst    = None

	@property
	@abstractmethod
	def required_tools(self):
		raise NotImplementedError('Platform must implement this property')


	def __init__(self) -> None:
		super().__init__(self.resources, self.connectors)

		self.extra_files = OrderedDict()

		self._prepared   = False

	@property
	def default_clk_constraint(self) -> Clock:
		if self.default_clk is None:
			raise AttributeError(f'Platform \'{type(self).__name__}\' does not define a default clock')

		return self.lookup(self.default_clk).clock

	@property
	def default_clk_frequency(self) -> float:
		constraint = self.default_clk_constraint
		if constraint is None:
			raise AttributeError(f'Platform \'{type(self).__name__}\' does not constrain its default clock')

		return constraint.frequency

	def add_file(self, filename : str, content : Union[str, bytes, IO]) -> None:
		if not isinstance(filename, str):
			raise TypeError(f'File name must be a string, not {filename!r}')
		if hasattr(content, 'read'):
			content = content.read()
		elif not isinstance(content, (str, bytes)):
			raise TypeError(f'File contents must be str, bytes, or a file-like object, not {content!r}')

		if filename in self.extra_files:
			if self.extra_files[filename] != content:
				raise ValueError(f'File {filename!r} already exists')
		else:
			self.extra_files[filename] = content

	def iter_files(self, *suffixes : str) -> Iterable[str]:
		for filename in self.extra_files:
			if filename.endswith(suffixes):
				yield filename

	@property
	def _deprecated_toolchain_env_var(self) -> str:
		return f'AMARANTH_ENV_{tool_env_var(self.toolchain)}'

	@property
	def _toolchain_env_var(self) -> str:
		return f'TORII_ENV_{tool_env_var(self.toolchain)}'

	def build(
		self, elaboratable : Union[Fragment, Elaboratable], name : str = 'top', build_dir : str = 'build',
		do_build : bool = True, program_opts : Optional[Dict[str, str]] = None, do_program : bool = False, **kwargs
	) -> Union[BuildPlan, BuildProducts, None]:
		# The following code performs a best-effort check for presence of required tools upfront,
		# before performing any build actions, to provide a better diagnostic. It does not handle
		# several corner cases:
		#  1. `require_tool` does not source toolchain environment scripts, so if such a script
		#     is used, the check is skipped, and `execute_local()` may fail;
		#  2. if the design is not built (do_build=False), most of the tools are not required and
		#     in fact might not be available if the design will be built manually with a different
		#     environment script specified, or on a different machine; however, Yosys is required
		#     by virtually every platform anyway, to provide debug Verilog output, and `prepare()`
		#     may fail.
		# This is OK because even if `require_tool` succeeds, the toolchain might be broken anyway.
		# The check only serves to catch common errors earlier.
		if do_build and (
			self._deprecated_toolchain_env_var not in os.environ and
			self._toolchain_env_var not in os.environ
		):
			for tool in self.required_tools:
				require_tool(tool)

		plan = self.prepare(elaboratable, name, **kwargs)
		if not do_build:
			return plan

		products = plan.execute_local(build_dir)
		if not do_program:
			return products

		self.toolchain_program(products, name, **(program_opts or {}))

	def has_required_tools(self) -> bool:
		if (self._deprecated_toolchain_env_var in os.environ or
				self._toolchain_env_var in os.environ):
			return True
		return all(has_tool(name) for name in self.required_tools)

	def create_missing_domain(self, name : str) -> Module:
		# Simple instantiation of a clock domain driven directly by the board clock and reset.
		# This implementation uses a single ResetSynchronizer to ensure that:
		#   * an external reset is definitely synchronized to the system clock;
		#   * release of power-on reset, which is inherently asynchronous, is synchronized to
		#     the system clock.
		# Many device families provide advanced primitives for tackling reset. If these exist,
		# they should be used instead.
		if name == 'sync' and self.default_clk is not None:
			clk_i = self.request(self.default_clk).i
			if self.default_rst is not None:
				rst_i = self.request(self.default_rst).i
			else:
				rst_i = Const(0)

			m = Module()
			m.domains += ClockDomain('sync')
			m.d.comb += ClockSignal('sync').eq(clk_i)
			m.submodules.reset_sync = ResetSynchronizer(rst_i, domain = 'sync')
			return m

	def prepare(
		self, elaboratable : Union[Fragment, Elaboratable], name : str = 'top', **kwargs
	) -> BuildPlan:
		assert not self._prepared
		self._prepared = True

		fragment = Fragment.get(elaboratable, self)
		fragment = SampleLowerer()(fragment)
		fragment._propagate_domains(self.create_missing_domain, platform = self)
		fragment = DomainLowerer()(fragment)

		def add_pin_fragment(pin, pin_fragment):
			pin_fragment = Fragment.get(pin_fragment, self)
			if not isinstance(pin_fragment, Instance):
				pin_fragment.flatten = True
			fragment.add_subfragment(pin_fragment, name = f'pin_{pin.name}')

		for pin, port, attrs, invert in self.iter_single_ended_pins():
			if pin.dir == 'i':
				add_pin_fragment(pin, self.get_input(pin, port, attrs, invert))
			if pin.dir == 'o':
				add_pin_fragment(pin, self.get_output(pin, port, attrs, invert))
			if pin.dir == 'oe':
				add_pin_fragment(pin, self.get_tristate(pin, port, attrs, invert))
			if pin.dir == 'io':
				add_pin_fragment(pin, self.get_input_output(pin, port, attrs, invert))

		for pin, port, attrs, invert in self.iter_differential_pins():
			if pin.dir == 'i':
				add_pin_fragment(pin, self.get_diff_input(pin, port, attrs, invert))
			if pin.dir == 'o':
				add_pin_fragment(pin, self.get_diff_output(pin, port, attrs, invert))
			if pin.dir == 'oe':
				add_pin_fragment(pin, self.get_diff_tristate(pin, port, attrs, invert))
			if pin.dir == 'io':
				add_pin_fragment(pin, self.get_diff_input_output(pin, port, attrs, invert))

		fragment._propagate_ports(ports = self.iter_ports(), all_undef_as_ports = False)
		return self.toolchain_prepare(fragment, name, **kwargs)

	@abstractmethod
	def toolchain_prepare(self, fragment : Fragment, name : str, **kwargs) -> BuildPlan:
		'''
		Convert the ``fragment`` and constraints recorded in this :class:`Platform` into
		a :class:`BuildPlan`.
		'''
		raise NotImplementedError # :nocov:

	def toolchain_program(self, products : BuildProducts, name : str, **kwargs) -> None:
		'''
		Extract bitstream for fragment ``name`` from ``products`` and download it to a target.
		'''
		raise NotImplementedError(f'Platform \'{type(self).__name__}\' does not support programming')

	def _check_feature(
		self, feature : str, pin : Pin, attrs : Attrs, valid_xdrs : Tuple[int], valid_attrs : Optional[str]
	) -> None:
		if len(valid_xdrs) == 0:
			raise NotImplementedError(f'Platform \'{type(self).__name__}\' does not support {feature}')

		elif pin.xdr not in valid_xdrs:
			raise NotImplementedError(f'Platform \'{type(self).__name__}\' does not support {feature} for XDR {pin.xdr}')

		if not valid_attrs and attrs:
			raise NotImplementedError(f'Platform \'{type(self).__name__}\' does not support attributes for {feature}')

	@staticmethod
	def _invert_if(invert : bool, value):
		if invert:
			return ~value
		else:
			return value

	def get_input(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> Module:
		self._check_feature('single-ended input', pin, attrs, valid_xdrs = (0,), valid_attrs = None)

		m = Module()
		m.d.comb += pin.i.eq(self._invert_if(invert, port))
		return m

	def get_output(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> Module:
		self._check_feature('single-ended output', pin, attrs, valid_xdrs = (0,), valid_attrs = None)

		m = Module()
		m.d.comb += port.eq(self._invert_if(invert, pin.o))
		return m

	def get_tristate(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> Module:
		self._check_feature('single-ended tristate', pin, attrs, valid_xdrs = (0,), valid_attrs = None)

		m = Module()
		m.submodules += Instance('$tribuf',
			p_WIDTH = pin.width,
			i_EN    = pin.oe,
			i_A     = self._invert_if(invert, pin.o),
			o_Y     = port,
		)
		return m

	def get_input_output(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> Module:
		self._check_feature('single-ended input/output', pin, attrs, valid_xdrs = (0,), valid_attrs = None)

		m = Module()
		m.submodules += Instance('$tribuf',
			p_WIDTH = pin.width,
			i_EN    = pin.oe,
			i_A     = self._invert_if(invert, pin.o),
			o_Y     = port,
		)
		m.d.comb += pin.i.eq(self._invert_if(invert, port))
		return m

	def get_diff_input(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> None:
		self._check_feature('differential input', pin, attrs, valid_xdrs = (), valid_attrs = None)

	def get_diff_output(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> None:
		self._check_feature('differential output', pin, attrs, valid_xdrs = (), valid_attrs = None)

	def get_diff_tristate(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> None:
		self._check_feature('differential tristate', pin, attrs, valid_xdrs = (), valid_attrs = None)

	def get_diff_input_output(
		self, pin : Pin, port : Record, attrs : Attrs, invert : bool
	) -> None:
		self._check_feature('differential input/output', pin, attrs, valid_xdrs = (), valid_attrs = None)


class TemplatedPlatform(Platform):
	@property
	@abstractmethod
	def toolchain(self) ->  Optional[str]:
		raise NotImplementedError('Platform must implement this property')

	@property
	@abstractmethod
	def file_templates(self) -> Dict[str, str]:
		raise NotImplementedError('Platform must implement this property')

	@property
	@abstractmethod
	def command_templates(self) -> List[str]:
		raise NotImplementedError('Platform must implement this property')

	build_script_templates = {
		'build_{{name}}.sh': '''
			# {{autogenerated}}
			set -e{{verbose("x")}}
			[ -n "${{platform._deprecated_toolchain_env_var}}" ] && . "${{platform._deprecated_toolchain_env_var}}"
			[ -n "${{platform._toolchain_env_var}}" ] && . "${{platform._toolchain_env_var}}"
			{{emit_commands("sh")}}
		''',
		'build_{{name}}.bat': '''
			@rem {{autogenerated}}
			{{quiet("@echo off")}}
			if defined {{platform._deprecated_toolchain_env_var}} call %{{platform._deprecated_toolchain_env_var}}%
			if defined {{platform._toolchain_env_var}} call %{{platform._toolchain_env_var}}%
			{{emit_commands("bat")}}
		''',
	}

	def iter_clock_constraints(self) -> Generator[
		Tuple[str, Signal, float], None, None
	]:
		for net_signal, port_signal, frequency in super().iter_clock_constraints():
			# Skip any clock constraints placed on signals that are never used in the design.
			# Otherwise, it will cause a crash in the vendor platform if it supports clock
			# constraints on non-port nets.
			if net_signal not in self._name_map:
				continue
			yield (net_signal, port_signal, frequency)

	def toolchain_prepare(self, fragment : Fragment, name : str, **kwargs) -> BuildPlan:
		# Restrict the name of the design to a strict alphanumeric character set. Platforms will
		# interpolate the name of the design in many different contexts: filesystem paths, Python
		# scripts, Tcl scripts, ad-hoc constraint files, and so on. It is not practical to add
		# escaping code that handles every one of their edge cases, so make sure we never hit them
		# in the first place.
		invalid_char = re.match(r'[^A-Za-z0-9_]', name)
		if invalid_char:
			raise ValueError(
				f'Design name {name!r} contains invalid character {invalid_char.group(0)!r}; only alphanumeric '
				'characters are valid in design names'
			)

		# This notice serves a dual purpose: to explain that the file is autogenerated,
		# and to incorporate the Torii version into generated code.
		autogenerated = f'Automatically generated by Torii {__version__}. Do not edit.'

		rtlil_text, self._name_map = rtlil.convert_fragment(fragment, name = name)

		# Retrieve an override specified in either the environment or as a kwarg.
		# expected_type parameter is used to assert the type of kwargs, passing `None` will disable
		# type checking.
		_ETYPE = TypeVar('_ETYPE')

		def _extract_override(
			var : str, *, expected_type : Type[_ETYPE]
		) -> Union[jinja2.Undefined, _ETYPE]:
			deprecated_var_env = f'AMARANTH_{var}'
			var_env = 'TORII_{var}'
			if deprecated_var_env in os.environ or var_env in os.environ:
				# On Windows, there is no way to define an "empty but set" variable; it is tempting
				# to use a quoted empty string, but it doesn't do what one would expect. Recognize
				# this as a useful pattern anyway, and treat `set VAR=""` on Windows the same way
				# `export VAR=` is treated on Linux.
				if var_env in os.environ:
					var_env_value = os.environ[var_env]
				elif deprecated_var_env in os.environ:
					var_env_value = os.environ[deprecated_var_env]
				return re.sub(r'^\"\"$', '', var_env_value)
			elif var in kwargs:
				if not isinstance(kwargs[var], expected_type) and expected_type is not None:
					raise TypeError(f'Override \'{var}\' must be a {expected_type.__name__}, not {kwargs[var]!r}')
				else:
					return kwargs[var]
			else:
				return jinja2.Undefined(name = var)

		def get_override(var : str) -> str:
			value = _extract_override(var, expected_type = str)
			return value

		def get_override_flag(var : str) -> bool:
			value = _extract_override(var, expected_type = bool)
			if isinstance(value, str):
				value = value.lower()
				if value in ('0', 'no', 'n', 'false', ''):
					return False
				if value in ('1', 'yes', 'y', 'true'):
					return True
				else:
					raise ValueError(f'Override \'{var}\' must be one of ("0", "n", "no", "false", "") or ("1", "y", "yes", "true"), not {value!r}')
			return value

		def emit_rtlil() -> str:
			return rtlil_text

		def emit_verilog(opts : Tuple[str] = ()) -> str:
			return verilog._convert_rtlil_text(
				rtlil_text, strip_internal_attrs = True, write_verilog_opts = opts
			)

		def emit_debug_verilog(opts : str = ()) -> str:
			if not get_override_flag('debug_verilog'):
				return '/* Debug Verilog generation was disabled. */'
			else:
				return verilog._convert_rtlil_text(
					rtlil_text, strip_internal_attrs = False, write_verilog_opts = opts
				)

		def emit_commands(syntax : Literal['sh', 'bat']) -> str:
			commands = []

			for name in self.required_tools:
				env_var = tool_env_var(name)
				if syntax == 'sh':
					template = ': ${{{env_var}:={name}}}'
				elif syntax == 'bat':
					template = \
						'if [%{env_var}%] equ [\"\"] set {env_var}=\n' \
						'if [%{env_var}%] equ [] set {env_var}={name}'
				else:
					assert False
				commands.append(template.format(env_var = env_var, name = name))

			for index, command_tpl in enumerate(self.command_templates):
				command = render(
					command_tpl, origin = f'<command#{index + 1}>', syntax = syntax
				)
				command = re.sub(r'\s+', ' ', command)
				if syntax == 'sh':
					commands.append(command)
				elif syntax == 'bat':
					commands.append(command + ' || exit /b')
				else:
					assert False

			return '\n'.join(commands)

		@jinja2.pass_context
		def invoke_tool(context, name : str) -> str:
			env_var = tool_env_var(name)
			if context.parent['syntax'] == 'sh':
				return '"${env_var}"'
			elif context.parent['syntax'] == 'bat':
				return '%{env_var}%'
			else:
				assert False

		def options(opts : Union[str, Iterable[str]]) -> str:
			if isinstance(opts, str):
				return opts
			else:
				return ' '.join(opts)

		def hierarchy(signal, separator):
			return separator.join(self._name_map[signal][1:])

		def verbose(arg : str) -> Union[jinja2.Undefined, str]:
			if get_override_flag('verbose'):
				return arg
			else:
				return jinja2.Undefined(name = 'quiet')

		def quiet(arg : str) -> Union[jinja2.Undefined, str]:
			if get_override_flag('verbose'):
				return jinja2.Undefined(name = 'quiet')
			else:
				return arg

		def render(
			source : str, origin : str, syntax : Optional[Literal['sh', 'bat']] = None
		) -> str:
			try:
				source   = textwrap.dedent(source).strip()
				compiled = jinja2.Template(
					source,
					trim_blocks = True,
					lstrip_blocks = True,
					undefined = jinja2.StrictUndefined
				)
				compiled.environment.filters['options']      = options
				compiled.environment.filters['hierarchy']    = hierarchy
				compiled.environment.filters['ascii_escape'] = ascii_escape
				compiled.environment.filters['tcl_escape']   = tcl_escape
				compiled.environment.filters['tcl_quote']    = tcl_quote
			except jinja2.TemplateSyntaxError as e:
				e.args = (f'{e.message} (at {origin}:{e.lineno})',)
				raise
			return compiled.render({
				'name'              : name,
				'platform'          : self,
				'emit_rtlil'        : emit_rtlil,
				'emit_verilog'      : emit_verilog,
				'emit_debug_verilog': emit_debug_verilog,
				'emit_commands'     : emit_commands,
				'syntax'            : syntax,
				'invoke_tool'       : invoke_tool,
				'get_override'      : get_override,
				'get_override_flag' : get_override_flag,
				'verbose'           : verbose,
				'quiet'             : quiet,
				'autogenerated'     : autogenerated,
			})

		plan = BuildPlan(script = f'build_{name}')
		for filename_tpl, content_tpl in self.file_templates.items():
			plan.add_file(
				render(filename_tpl, origin = filename_tpl),
				render(content_tpl, origin = content_tpl)
			)
		for filename, content in self.extra_files.items():
			plan.add_file(filename, content)
		return plan
