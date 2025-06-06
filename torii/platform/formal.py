# SPDX-License-Identifier: BSD-2-Clause

from typing       import Literal

from ..build.plat import TemplatedPlatform
from ..build.run  import BuildPlan, BuildProducts
from ..hdl.ir     import Elaboratable, Fragment

__all__ = (
	'FormalPlatform',
)

# TODO(aki): Support other engines, not just smtbmc
class FormalPlatform(TemplatedPlatform):
	'''
	.. rubric:: sby toolchain

	Required tools:
		* ``yosys``
		* ``yosys-abc``
		* ``yosys-smtbmc``
		* ``sby``
		* ``yices``

	The environment is populated by running the script specified in the environment variable
	``TORII_ENV_SBY``, if present.

	Available overrides:
		* ``solver``: specifies the solver for ``smtbmc`` to use, default is ``yices``
		* ``smtbmc_opts``: adds extra options for the ``sby`` ``smtbmc`` engine.
		* ``depth``: specifies the bounded model checkers max depth.
		* ``script_prelude``: adds extra lines to the ``sby`` script before everything else.
		* ``script_interim``: adds extra lines to the ``sby`` script after file reads but before prepare.
		* ``script_epilogue``: adds extra lines to the ``sby`` script after everything else.
		* ``read_verilog_opts``: adds options for ``read_verilog`` Yosys command.
		* ``sby_opts``: adds extra options for ``sby``.
		* ``sby_jobs``: specifies the number of parallel jobs to run.

	see https://symbiyosys.readthedocs.io/en/latest/reference.html for additional possible overrides.

	Intermediary products:
		* ``{{name}}.il``: generated design RTLIL.
		* ``{{name}}.debug.v``: if ``debug_verilog`` is set, this contains generated design verilog.
		* ``build_{{name}}.sh``: build invocations for Unix-likes.
		* ``build_{{name}}.bat``: build invocations for Windows.

	Build products:
		* ``{{name}}_formal/*``: The results of the SBY run.

	'''

	# These are not used in formal mode, so we define them here.
	resources = []
	connectors = []

	toolchain = 'sby'
	_sby_required_tools = (
		'yosys',
		'yosys-abc',
		'yosys-smtbmc',
		'sby',
		'yices'
	)

	_sby_file_templates = {
		**TemplatedPlatform.build_script_templates,
		'{{name}}.il': r'''
			# {{autogenerated}}
			{{emit_rtlil()}}
		''',
		'{{name}}.debug.v': r'''
			/* {{autogenerated}} */
			{{emit_debug_verilog()}}
		''',
		'{{name}}.sby': r'''
			[options]
			mode {{platform.mode}}
			expect {{get_override("expect")|default("pass")}}
			{% if get_override_int("timeout") %}
			timeout {{get_override_int("timeout")}}
			{% endif %}
			multiclock {{get_override("multiclock")|default("off")}}
			wait {{get_override("wait")|default("off")}}
			vcd {{get_override("vcd")|default("on")}}
			vcd_sim {{get_override("vcd_sim")|default("off")}}
			fst {{get_override("vcd")|default("off")}}
			aigsmt {{get_override("aigsmt")|default("yices")}}
			{% if get_override("tbtop") %}
			tbtop {{get_override("tbtop")}}
			{% endif %}

			{% if platform.mode in ("bmc", "prove", "cover")  %}
			depth {{get_override_int("depth")|default("10")}}
			append {{get_override_int("append")|default("0")}}
			append_assume {{get_override("append_assume")|default("on")}}
			{% endif %}

			[engines]
			{% if platform.mode in ("bmc", "prove") %}
			smtbmc {{get_override("smtbmc_opts")|options}} {{get_override("solver")|default("yices")}}
			{% endif %}

			[script]
			{% for line in get_override_list("script_prelude") %}
				{{line}}
			{% endfor %}
			{% for file in platform.iter_files(".v") -%}
				read_verilog -formal {{get_override("read_verilog_opts")|options}} {{file}}
			{% endfor %}
			{% for file in platform.iter_files(".sv") -%}
				read_verilog -formal {{get_override("read_verilog_opts")|options}} -sv {{file}}
			{% endfor %}
			{% for file in platform.iter_files(".il") -%}
				read_rtlil {{file}}
			{% endfor %}
			read_rtlil {{name}}.il
			{% for line in get_override_list("script_interim") %}
				{{line}}
			{% endfor %}
			prep -top {{name}}
			setattr -unset init w:* a:torii.sample_reg %d
			{% for line in get_override_list("script_epilogue") %}
				{{line}}
			{% endfor %}

			[files]
			{{name}}.il
			{% for file in platform.iter_files(".v") -%}
				{{file}}
			{% endfor %}
			{% for file in platform.iter_files(".sv") -%}
				{{file}}
			{% endfor %}
			{% for file in platform.iter_files(".il") -%}
				{{file}}
			{% endfor %}
		'''
	}

	_sby_command_templates = [
		r'''
		{{invoke_tool("sby")}}
			-f
			-j {{get_override_int("sby_jobs")|default("1")}}
			-d {{name}}_formal
			{{get_override("sby_opts")|options}}
			{{name}}.sby
		'''
	]

	def __init__(self, mode: Literal['bmc', 'prove', 'cover', 'live']) -> None:
		super().__init__()

		self.mode = mode

	@property
	def required_tools(self) -> list[str]:
		return self._sby_required_tools

	@property
	def file_templates(self) -> dict[str, str]:
		return self._sby_file_templates

	@property
	def command_templates(self) -> list[str]:
		return self._sby_command_templates

	def build(self, *args, **kwargs) -> BuildPlan | BuildProducts | None:
		self._build_dir = kwargs.get('build_dir', 'build')
		return super().build(*args, **kwargs, formal = True)

	def prepare(
		self, elaboratable: Fragment | Elaboratable, name: str = 'top', **kwargs
	) -> BuildPlan:
		fragment = Fragment.get(elaboratable, self, formal = True)
		return self.toolchain_prepare(fragment.prepare(), name, **kwargs)

	def toolchain_prepare(self, fragment: Fragment, name: str, **kwargs) -> BuildPlan:
		# Propagate ports up so the formal tools have something to grab ahold of
		a_ports = kwargs.get('ports', None)
		if a_ports is not None:
			fragment._propagate_ports(ports = a_ports, all_undef_as_ports = False)

		return super().toolchain_prepare(fragment, name, **kwargs)
