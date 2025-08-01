# SPDX-License-Identifier: BSD-2-Clause

from abc        import abstractmethod
from typing     import Literal

from ...build   import Attrs, TemplatedPlatform
from ...hdl     import ClockDomain, ClockSignal, Const, Instance, Module, Record, ResetSignal, Signal
from ...lib.cdc import ResetSynchronizer
from ...lib.io  import Pin

__all__ = (
	'XilinxPlatform',
)

class XilinxPlatform(TemplatedPlatform):
	'''
	.. rubric:: Vivado toolchain

	Required tools:
		* ``vivado``

	The environment is populated by running the script specified in the environment variable
	``TORII_ENV_VIVADO``, if present.

	Available overrides:
		* ``script_after_read``: inserts commands after ``read_xdc`` in Tcl script.
		* ``synth_design_opts``: sets options for ``synth_design``.
		* ``script_after_synth``: inserts commands after ``synth_design`` in Tcl script.
		* ``script_after_place``: inserts commands after ``place_design`` in Tcl script.
		* ``script_after_route``: inserts commands after ``route_design`` in Tcl script.
		* ``script_before_bitstream``: inserts commands before ``write_bitstream`` in Tcl script.
		* ``script_after_bitstream``: inserts commands after ``write_bitstream`` in Tcl script.
		* ``add_constraints``: inserts commands in XDC file.
		* ``vivado_opts``: adds extra options for ``vivado``.

	Build products:
		* ``{{name}}.log``: Vivado log.
		* ``{{name}}_timing_synth.rpt``: Vivado report.
		* ``{{name}}_utilization_hierarchical_synth.rpt``: Vivado report.
		* ``{{name}}_utilization_synth.rpt``: Vivado report.
		* ``{{name}}_utilization_hierarchical_place.rpt``: Vivado report.
		* ``{{name}}_utilization_place.rpt``: Vivado report.
		* ``{{name}}_io.rpt``: Vivado report.
		* ``{{name}}_control_sets.rpt``: Vivado report.
		* ``{{name}}_clock_utilization.rpt``:  Vivado report.
		* ``{{name}}_route_status.rpt``: Vivado report.
		* ``{{name}}_drc.rpt``: Vivado report.
		* ``{{name}}_methodology.rpt``: Vivado report.
		* ``{{name}}_timing.rpt``: Vivado report.
		* ``{{name}}_power.rpt``: Vivado report.
		* ``{{name}}_route.dcp``: Vivado design checkpoint.
		* ``{{name}}.bit``: binary bitstream with metadata.
		* ``{{name}}.bin``: binary bitstream.

	.. rubric:: ISE toolchain

	Required tools:
		* ``xst``
		* ``ngdbuild``
		* ``map``
		* ``par``
		* ``bitgen``

	The environment is populated by running the script specified in the environment variable
	``TORII_ENV_ISE``, if present.

	Available overrides:
		* ``script_after_run``: inserts commands after ``run`` in XST script.
		* ``add_constraints``: inserts commands in UCF file.
		* ``xst_opts``: adds extra options for ``xst``.
		* ``ngdbuild_opts``: adds extra options for ``ngdbuild``.
		* ``map_opts``: adds extra options for ``map``.
		* ``par_opts``: adds extra options for ``par``.
		* ``bitgen_opts``: adds extra and overrides default options for ``bitgen``;
		  default options: ``-g Compress``.

	Build products:
		* ``{{name}}.srp``: synthesis report.
		* ``{{name}}.ngc``: synthesized RTL.
		* ``{{name}}.bld``: NGDBuild log.
		* ``{{name}}.ngd``: design database.
		* ``{{name}}_map.map``: MAP log.
		* ``{{name}}_map.mrp``: mapping report.
		* ``{{name}}_map.ncd``: mapped netlist.
		* ``{{name}}.pcf``: physical constraints.
		* ``{{name}}_par.par``: PAR log.
		* ``{{name}}_par_pad.txt``: I/O usage report.
		* ``{{name}}_par.ncd``: place and routed netlist.
		* ``{{name}}.drc``: DRC report.
		* ``{{name}}.bgn``: BitGen log.
		* ``{{name}}.bit``: binary bitstream with metadata.
		* ``{{name}}.bin``: raw binary bitstream.

	.. rubric:: Symbiflow toolchain

	Required tools:
		* ``symbiflow_synth``
		* ``symbiflow_pack``
		* ``symbiflow_place``
		* ``symbiflow_route``
		* ``symbiflow_write_fasm``
		* ``symbiflow_write_bitstream``

	The environment is populated by running the script specified in the environment variable
	``TORII_ENV_SYMBIFLOW``, if present.

	Available overrides:
		* ``add_constraints``: inserts commands in XDC file.

	.. rubric:: yosys_nextpnr toolchain

	Required tools:
		* ``yosys``
		* ``nextpnr-xilinx``
		* ``fasm2frames``
		* ``xc7frames2bit``

	The environment is populated by running the script specified in the environment variable
	``TORII_ENV_YOSYS_NEXTPNR``, if present.

	Available overrides:
		* ``nextpnr_db_dir``: overrides nextpnr-xilinx chip-db path.
		* ``prjxray_db_dir``: overrides prjxray db path prefix.
		* ``read_verilog_opts``: adds options for ``read_verilog`` Yosys command.
		* ``script_after_read``: inserts commands after ``read_verilog`` in Yosys script.
		* ``synth_opts``: adds options for ``synth_xilinx`` Yosys command.
		* ``script_after_synth``: inserts commands after ``synth_xilinx`` in Yosys script.
		* ``yosys_opts``: adds extra options for ``yosys``.
		* ``nextpnr_opts``: adds extra options for ``nextpnr-xilinx``.
		* ``fasm2frames_opts``: adds extra options for ``fasm2frames``.
		* ``xc7frames2bit_opts``: adds extra options for ``xc7frames2bit``.

	''' # noqa: E101

	toolchain = None # selected when creating platform

	@property
	@abstractmethod
	def device(self) -> str:
		raise NotImplementedError('Platform must implement this property')

	@property
	@abstractmethod
	def package(self) -> str:
		raise NotImplementedError('Platform must implement this property')

	@property
	@abstractmethod
	def speed(self) -> str:
		raise NotImplementedError('Platform must implement this property')

	@property
	def _part(self) -> str:
		if self.family in { 'ultrascale', 'ultrascaleplus' }:
			return f'{self.device}-{self.package}-{self.speed}'
		else:
			return f'{self.device}{self.package}-{self.speed}'

	# Vivado templates

	_vivado_required_tools = [ 'vivado' ]
	_vivado_file_templates = {
		**TemplatedPlatform.build_script_templates,
		'build_{{name}}.sh': r'''
			#!/bin/sh
			# {{autogenerated}}
			set -e{{verbose("x")}}
			if [ -z "$BASH" ] ; then exec /bin/bash "$0" "$@"; fi
			[ -n "${{platform._toolchain_env_var}}" ] && . "${{platform._toolchain_env_var}}"
			{{emit_commands("sh")}}
		''',
		'{{name}}.v': r'''
			/* {{autogenerated}} */
			{{emit_verilog()}}
		''',
		'{{name}}.debug.v': r'''
			/* {{autogenerated}} */
			{{emit_debug_verilog()}}
		''',
		'{{name}}.tcl': r'''
			# {{autogenerated}}
			create_project -force -name {{name}} -part {{platform._part}}
			{% for file in platform.iter_files(".v", ".sv", ".vhd", ".vhdl") -%}
				add_files {{file|tcl_escape}}
			{% endfor %}
			add_files {{name}}.v
			read_xdc {{name}}.xdc
			{% for file in platform.iter_files(".xdc") -%}
				read_xdc {{file|tcl_escape}}
			{% endfor %}
			{{get_override("script_after_read")|default("# (script_after_read placeholder)")}}
			synth_design -top {{name}} {{get_override("synth_design_opts")}}
			foreach cell [get_cells -quiet -hier -filter {torii.vivado.false_path == "TRUE"}] {
				set_false_path -to $cell
			}
			foreach cell [get_cells -quiet -hier -filter {torii.vivado.max_delay != ""}] {
				set clock [get_clocks -of_objects \
					[all_fanin -flat -startpoints_only [get_pin $cell/D]]]
				if {[llength $clock] != 0} {
					set_max_delay -datapath_only -from $clock \
						-to [get_cells $cell] [get_property torii.vivado.max_delay $cell]
				}
			}
			{{get_override("script_after_synth")|default("# (script_after_synth placeholder)")}}
			report_timing_summary -file {{name}}_timing_synth.rpt
			report_utilization -hierarchical -file {{name}}_utilization_hierarchical_synth.rpt
			report_utilization -file {{name}}_utilization_synth.rpt
			opt_design
			place_design
			{{get_override("script_after_place")|default("# (script_after_place placeholder)")}}
			report_utilization -hierarchical -file {{name}}_utilization_hierarchical_place.rpt
			report_utilization -file {{name}}_utilization_place.rpt
			report_io -file {{name}}_io.rpt
			report_control_sets -verbose -file {{name}}_control_sets.rpt
			report_clock_utilization -file {{name}}_clock_utilization.rpt
			route_design
			{{get_override("script_after_route")|default("# (script_after_route placeholder)")}}
			phys_opt_design
			report_timing_summary -no_header -no_detailed_paths
			write_checkpoint -force {{name}}_route.dcp
			report_route_status -file {{name}}_route_status.rpt
			report_drc -file {{name}}_drc.rpt
			report_methodology -file {{name}}_methodology.rpt
			report_timing_summary -datasheet -max_paths 10 -file {{name}}_timing.rpt
			report_power -file {{name}}_power.rpt
			{{get_override("script_before_bitstream")|default("# (script_before_bitstream placeholder)")}}
			write_bitstream -force -bin_file {{name}}.bit
			{{get_override("script_after_bitstream")|default("# (script_after_bitstream placeholder)")}}
			quit
		''',
		'{{name}}.xdc': r'''
			# {{autogenerated}}
			{% for port_name, pin_name, attrs in platform.iter_port_constraints_bits() -%}
				set_property LOC {{pin_name}} [get_ports {{port_name|tcl_escape}}]
				{% for attr_name, attr_value in attrs.items() -%}
					set_property {{attr_name}} {{attr_value|tcl_escape}} [get_ports {{port_name|tcl_escape}}]
				{% endfor %}
			{% endfor %}
			{% for net_signal, port_signal, frequency in platform.iter_clock_constraints() -%}
				{% if port_signal is not none -%}
					create_clock -name {{port_signal.name|ascii_escape}} -period {{1000000000/frequency}} [get_ports {{port_signal.name|tcl_escape}}]
				{% else -%}
					create_clock -name {{net_signal.name|ascii_escape}} -period {{1000000000/frequency}} [get_nets {{net_signal|hierarchy("/")|tcl_escape}}]
				{% endif %}
			{% endfor %}
			{{get_override("add_constraints")|default("# (add_constraints placeholder)")}}
		''' # noqa: E501
	}
	_vivado_command_templates = [
		r'''
		{{invoke_tool("vivado")}}
			{{verbose("-verbose")}}
			{{get_override("vivado_opts")|options}}
			-mode batch
			-log {{name}}.log
			-source {{name}}.tcl
		'''
	]

	# ISE toolchain

	_ise_required_tools = [
		'xst',
		'ngdbuild',
		'map',
		'par',
		'bitgen',
	]
	_ise_file_templates = {
		**TemplatedPlatform.build_script_templates,
		'build_{{name}}.sh': r'''
			#!/bin/sh
			# {{autogenerated}}
			set -e{{verbose("x")}}
			if [ -z "$BASH" ] ; then exec /bin/bash "$0" "$@"; fi
			[ -n "${{platform._toolchain_env_var}}" ] && . "${{platform._toolchain_env_var}}"
			{{emit_commands("sh")}}
		''',
		'{{name}}.v': r'''
			/* {{autogenerated}} */
			{{emit_verilog()}}
		''',
		'{{name}}.debug.v': r'''
			/* {{autogenerated}} */
			{{emit_debug_verilog()}}
		''',
		'{{name}}.prj': r'''
			# {{autogenerated}}
			{% for file in platform.iter_files(".vhd", ".vhdl") -%}
				vhdl work {{file}}
			{% endfor %}
			{% for file in platform.iter_files(".v") -%}
				verilog work {{file}}
			{% endfor %}
			verilog work {{name}}.v
		''',
		'{{name}}.xst': r'''
			# {{autogenerated}}
			run
			-ifn {{name}}.prj
			-ofn {{name}}.ngc
			-top {{name}}
			-use_new_parser yes
			-p {{platform.device}}{{platform.package}}-{{platform.speed}}
			{{get_override("script_after_run")|default("# (script_after_run placeholder)")}}
		''',
		'{{name}}.ucf': r'''
			# {{autogenerated}}
			{% for port_name, pin_name, attrs in platform.iter_port_constraints_bits() -%}
				{% set port_name = port_name|replace("[", "<")|replace("]", ">") -%}
				NET '{{port_name}}" LOC = {{pin_name}};
				{% for attr_name, attr_value in attrs.items() -%}
					NET '{{port_name}}" {{attr_name}} = {{attr_value}};
				{% endfor %}
			{% endfor %}
			{% for net_signal, port_signal, frequency in platform.iter_clock_constraints() -%}
				NET '{{net_signal|hierarchy("/")}}" TNM_NET = "PRD{{net_signal|hierarchy("/")}}";
				TIMESPEC "TS{{net_signal|hierarchy("__")}}" = PERIOD "PRD{{net_signal|hierarchy("/")}}" {{1000000000/frequency}} ns HIGH 50%;
			{% endfor %}
			{{get_override("add_constraints")|default("# (add_constraints placeholder)")}}
		''' # noqa: E501
	}
	_ise_command_templates = [
		r'''
		{{invoke_tool("xst")}}
			{{get_override("xst_opts")|options}}
			-ifn {{name}}.xst
		''',
		r'''
		{{invoke_tool("ngdbuild")}}
			{{quiet("-quiet")}}
			{{verbose("-verbose")}}
			{{get_override("ngdbuild_opts")|options}}
			-uc {{name}}.ucf
			{{name}}.ngc
		''',
		r'''
		{{invoke_tool("map")}}
			{{verbose("-detail")}}
			{{get_override("map_opts")|default([])|options}}
			-w
			-o {{name}}_map.ncd
			{{name}}.ngd
			{{name}}.pcf
		''',
		r'''
		{{invoke_tool("par")}}
			{{get_override("par_opts")|default([])|options}}
			-w
			{{name}}_map.ncd
			{{name}}_par.ncd
			{{name}}.pcf
		''',
		r'''
		{{invoke_tool("bitgen")}}
			{{get_override("bitgen_opts")|default(["-g Compress"])|options}}
			-w
			-g Binary:Yes
			{{name}}_par.ncd
			{{name}}.bit
		'''
	]

	# Symbiflow templates

	_symbiflow_part_map = {
		'xc7a35ticsg324-1L': 'xc7a35tcsg324-1', # Arty-A7
	}

	_symbiflow_required_tools = [
		'symbiflow_synth',
		'symbiflow_pack',
		'symbiflow_place',
		'symbiflow_route',
		'symbiflow_write_fasm',
		'symbiflow_write_bitstream',
	]
	_symbiflow_file_templates = {
		**TemplatedPlatform.build_script_templates,
		'{{name}}.v': r'''
			/* {{autogenerated}} */
			{{emit_verilog()}}
		''',
		'{{name}}.debug.v': r'''
			/* {{autogenerated}} */
			{{emit_debug_verilog()}}
		''',
		'{{name}}.pcf': r'''
			# {{autogenerated}}
			{% for port_name, pin_name, attrs in platform.iter_port_constraints_bits() -%}
				set_io {{port_name}} {{pin_name}}
			{% endfor %}
		''',
		'{{name}}.xdc': r'''
			# {{autogenerated}}
			{% for port_name, pin_name, attrs in platform.iter_port_constraints_bits() -%}
				{% for attr_name, attr_value in attrs.items() -%}
					set_property {{attr_name}} {{attr_value}} [get_ports {{port_name|tcl_escape}} }]
				{% endfor %}
			{% endfor %}
			{{get_override("add_constraints")|default("# (add_constraints placeholder)")}}
		''',
		'{{name}}.sdc': r'''
			# {{autogenerated}}
			{% for net_signal, port_signal, frequency in platform.iter_clock_constraints() -%}
				{% if port_signal is none -%}
					create_clock -period {{1000000000/frequency}} {{net_signal.name|ascii_escape}}
				{% endif %}
			{% endfor %}
		'''
	}
	_symbiflow_command_templates = [
		r'''
		{{invoke_tool("symbiflow_synth")}}
			-t {{name}}
			-v {% for file in platform.iter_files(".v", ".sv", ".vhd", ".vhdl") -%} {{file}} {% endfor %} {{name}}.v
			-p {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
			-x {{name}}.xdc
		''',
		r'''
		{{invoke_tool("symbiflow_pack")}}
			-e {{name}}.eblif
			-P {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
			-s {{name}}.sdc
		''',
		r'''
		{{invoke_tool("symbiflow_place")}}
			-e {{name}}.eblif
			-p {{name}}.pcf
			-n {{name}}.net
			-P {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
			-s {{name}}.sdc
		''',
		r'''
		{{invoke_tool("symbiflow_route")}}
			-e {{name}}.eblif
			-P {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
			-s {{name}}.sdc
		''',
		r'''
		{{invoke_tool("symbiflow_write_fasm")}}
			-e {{name}}.eblif
			-P {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
		''',
		r'''
		{{invoke_tool("symbiflow_write_bitstream")}}
			-f {{name}}.fasm
			-p {{platform._symbiflow_part_map.get(platform._part, platform._part)}}
			-b {{name}}.bit
		'''
	]

	# Yosys NextPNR prjxray templates

	_yosys_nextpnr_part_map = {
		'xc7a35ticsg324-1L':  'xc7a35tcsg324-1',  # Arty-A7 35t
		'xc7a100ticsg324-1L': 'xc7a100tcsg324-1', # Arty-A7 100t
	}

	_yosys_nextpnr_device = {
		'xc7a35ti':  'xc7a35t',
		'xc7a100ti': 'xc7a100t',
	}

	_yosys_nextpnr_family = {
		'xc7a': 'artix7',
		'xc7z': 'zynq7',
	}

	_yosys_nextpnr_required_tools = [
		'yosys',
		'nextpnr-xilinx',
		'fasm2frames',
		'xc7frames2bit'
	]

	_yosys_nextpnr_file_templates = {
		**TemplatedPlatform.build_script_templates,
		'build_{{name}}.sh': r'''
			#!/bin/sh
			# {{autogenerated}}
			set -e{{verbose("x")}}
			if [ -z "$BASH" ] ; then exec /bin/bash "$0" "$@"; fi
			[ -n "${{platform._toolchain_env_var}}" ] && . "${{platform._toolchain_env_var}}"
			{{emit_commands("sh")}}
		''',
		'{{name}}.v': r'''
			/* {{autogenerated}} */
			{{emit_verilog()}}
		''',
		'{{name}}.debug.v': r'''
			/* {{autogenerated}} */
			{{emit_debug_verilog()}}
		''',
		'{{name}}.xdc': r'''
			# {{autogenerated}}
			{% for port_name, pin_name, attrs in platform.iter_port_constraints_bits() -%}
				{% for attr_name, attr_value in attrs.items() -%}
					set_property {{attr_name}} {{attr_value}} [get_ports {{port_name|tcl_escape}}]
					set_property LOC {{pin_name}} [get_ports {{port_name|tcl_escape}}]
				{% endfor %}
			{% endfor %}
		''',
		'{{name}}.ys': r'''
			# {{autogenerated}}
			{% for file in platform.iter_files(".v") -%}
				read_verilog {{get_override("read_verilog_opts")|options}} {{file}}
			{% endfor %}
			{% for file in platform.iter_files(".sv") -%}
				read_verilog -sv {{get_override("read_verilog_opts")|options}} {{file}}
			{% endfor %}
			{% for file in platform.iter_files(".il") -%}
				read_rtlil {{file}}
			{% endfor %}
			read_verilog {{name}}.v
			{{get_override("script_after_read")|default("# (script_after_read placeholder)")}}
			synth_xilinx {{get_override("synth_opts")|options}} -flatten -abc9 -nobram -arch xc7 -top {{name}};
			{{get_override("script_after_synth")|default("# (script_after_synth placeholder)")}}
			write_json {{name}}.json
		'''
	}

	_yosys_nextpnr_command_templates = [
		r'''
		PRJXRAY_DB_DIR={{get_override("prjxray_db_dir")|default("/usr/share/nextpnr/prjxray-db")}}
		''',
		r'''
		NEXTPNR_CHIPDB_DIR={{get_override("nextpnr_db_dir")|default("/usr/share/nextpnr/xilinx-chipdb")}}
		''',
		r'''
		PART={{platform._yosys_nextpnr_part_map.get(platform._part, platform._part)}}
		''',
		r'''
		FAMILY={{platform._yosys_nextpnr_family[platform.device[:4]]}}
		''',
		r'''
		{{invoke_tool("yosys")}}
			{{quiet("-q")}}
			{{get_override("yosys_opts")|options}}
			-l {{name}}.rpt
			{{name}}.ys
		''',
		r'''
		{{invoke_tool("nextpnr-xilinx")}}
			{{quiet("--quiet")}}
			{{get_override("nextpnr_xilinx_opts")|options}}
			--log {{name}}.tim
			--chipdb "$NEXTPNR_CHIPDB_DIR/$PART.bin"
			--xdc {{name}}.xdc
			--json {{name}}.json
			--write {{name}}_routed.json
			--fasm {{name}}.fasm
		''',
		r'''
		{{invoke_tool("fasm2frames")}}
			{{get_override("fasm2frames_opts")}}
			--part $PART
			--db-root "$PRJXRAY_DB_DIR/$FAMILY" {{name}}.fasm > {{name}}.frames
		''',
		r'''
		{{invoke_tool("xc7frames2bit")}}
			{{get_override("xc7frames2bit_opts")}}
			--part_file "$PRJXRAY_DB_DIR/$FAMILY/$PART/part.yaml"
			--part_name $PART
			--frm_file {{name}}.frames
			--output_file {{name}}.bit
		''',
	]

	# Common logic

	def __init__(self, *, toolchain: Literal['Vivado', 'ISE', 'Symbiflow'] = None) -> None:
		super().__init__()

		# Determine device family.
		device = self.device.lower()
		# Remove the prefix.
		if device.startswith('xc'):
			device = device[2:]
		elif device.startswith('xa'):
			device = device[2:]
		elif device.startswith('xqr'):
			device = device[3:]
		elif device.startswith('xq'):
			device = device[2:]
		else:
			raise ValueError(f'Device \'{self.device}\' is not recognized')
		# Do actual name matching.
		if device.startswith('2vp'):
			self.family = 'virtex2p'
		elif device.startswith('2v'):
			self.family = 'virtex2'
		elif device.startswith('3sd'):
			self.family = 'spartan3adsp'
		elif device.startswith('3s'):
			if device.endswith('a'):
				self.family = 'spartan3a'
			elif device.endswith('e'):
				self.family = 'spartan3e'
			else:
				self.family = 'spartan3'
		elif device.startswith('4v'):
			self.family = 'virtex4'
		elif device.startswith('5v'):
			self.family = 'virtex5'
		elif device.startswith('6v'):
			self.family = 'virtex6'
		elif device.startswith('6s'):
			self.family = 'spartan6'
		elif device.startswith('7'):
			self.family = 'series7'
		elif device.startswith(('vu', 'ku')):
			if device.endswith('p'):
				self.family = 'ultrascaleplus'
			else:
				self.family = 'ultrascale'
		elif device.startswith(('zu', 'u', 'k26', 'au')):
			self.family = 'ultrascaleplus'
		elif device.startswith(('v', '2s')):
			# Match last to avoid conflict with ultrascale.
			# Yes, Spartan 2 is the same thing as Virtex.
			if device.endswith('e'):
				self.family = 'virtexe'
			else:
				self.family = 'virtex'

		ISE_FAMILIES = {
				'virtex', 'virtexe',
				'virtex2', 'virtex2p',
				'spartan3', 'spartan3e', 'spartan3a', 'spartan3adsp',
				'virtex4',
				'virtex5',
				'virtex6',
				'spartan6',
		}
		if toolchain is None:
			if self.family in ISE_FAMILIES:
				toolchain = 'ISE'
			else:
				toolchain = 'Vivado'

		if toolchain not in ('Vivado', 'ISE', 'Symbiflow', 'yosys_nextpnr'):
			raise ValueError(
				f'Unknown toolchain {toolchain}, must be one of '
				'\'Vivado\', \'ISE\', \'Symbiflow\', or \'yosys_nextpnr\''
			)

		if toolchain == 'Vivado':
			if self.family in ISE_FAMILIES:
				raise ValueError(f'Family \'{self.family}\' is not supported by the Vivado toolchain, please use ISE instead')
		elif toolchain == 'ISE':
			if self.family not in ISE_FAMILIES and self.family != "series7":
				raise ValueError(f'Family \'{self.family}\' is not supported by the ISE toolchain, please use Vivado instead')
		elif toolchain == "Symbiflow":
			if self.family != 'series7':
				raise ValueError(f'Family \'{self.family}\' is not supported by the Symbiflow toolchain')
		elif toolchain == 'yosys_nextpnr':
			if self.family != 'series7':
				raise ValueError(f'Family \'{self.family}\' is not supported by the yosys nextpnr toolchain')
		self.toolchain = toolchain

	@property
	def required_tools(self) -> list[str]:
		if self.toolchain not in ('Vivado', 'ISE', 'Symbiflow', 'yosys_nextpnr'):
			raise ValueError(
				f'Unknown toolchain {self.toolchain}, must be one of '
				'\'Vivado\', \'ISE\', \'Symbiflow\', or \'yosys_nextpnr\''
			)

		if self.toolchain == 'Vivado':
			return self._vivado_required_tools
		if self.toolchain == 'ISE':
			return self._ise_required_tools
		if self.toolchain == 'Symbiflow':
			return self._symbiflow_required_tools
		if self.toolchain == 'yosys_nextpnr':
			return self._yosys_nextpnr_required_tools

	@property
	def file_templates(self) -> dict[str, str]:
		if self.toolchain not in ('Vivado', 'ISE', 'Symbiflow', 'yosys_nextpnr'):
			raise ValueError(
				f'Unknown toolchain {self.toolchain}, must be one of '
				'\'Vivado\', \'ISE\', \'Symbiflow\', or \'yosys_nextpnr\''
			)

		if self.toolchain == 'Vivado':
			return self._vivado_file_templates
		if self.toolchain == 'ISE':
			return self._ise_file_templates
		if self.toolchain == 'Symbiflow':
			return self._symbiflow_file_templates
		if self.toolchain == 'yosys_nextpnr':
			return self._yosys_nextpnr_file_templates

	@property
	def command_templates(self) -> list[str]:
		if self.toolchain not in ('Vivado', 'ISE', 'Symbiflow', 'yosys_nextpnr'):
			raise ValueError(
				f'Unknown toolchain {self.toolchain}, must be one of '
				'\'Vivado\', \'ISE\', \'Symbiflow\', or \'yosys_nextpnr\''
			)

		if self.toolchain == 'Vivado':
			return self._vivado_command_templates
		if self.toolchain == 'ISE':
			return self._ise_command_templates
		if self.toolchain == 'Symbiflow':
			return self._symbiflow_command_templates
		if self.toolchain == 'yosys_nextpnr':
			return self._yosys_nextpnr_command_templates

	def create_missing_domain(self, name: str) -> Module:
		# Xilinx devices have a global write enable (GWE) signal that asserted during configuration
		# and de-asserted once it ends. Because it is an asynchronous signal (GWE is driven by logic
		# synchronous to configuration clock, which is not used by most designs), even though it is
		# a low-skew global network, its de-assertion may violate a setup/hold constraint with
		# relation to a user clock. The recommended solution is to use a BUFGCE driven by the EOS
		# signal (if available). For details, see:
		#   * https://www.xilinx.com/support/answers/44174.html
		#   * https://www.xilinx.com/support/documentation/white_papers/wp272.pdf

		STARTUP_PRIMITIVE = {
				'spartan6': 'STARTUP_SPARTAN6',
				'virtex4': 'STARTUP_VIRTEX4',
				'virtex5': 'STARTUP_VIRTEX5',
				'virtex6': 'STARTUP_VIRTEX6',
				'series7': 'STARTUPE2',
				'ultrascale': 'STARTUPE3',
				'ultrascaleplus': 'STARTUPE3',
		}

		if self.family not in STARTUP_PRIMITIVE or self.toolchain in ('Symbiflow', 'yosys_nextpnr'):
			# Spartan 3 and before lacks a STARTUP primitive with EOS output; use a simple ResetSynchronizer
			# in that case, as is the default.
			# Symbiflow does not support the STARTUPE2 primitive.
			return super().create_missing_domain(name)

		if name == 'sync' and self.default_clk is not None:
			clk_i = self.request(self.default_clk).i
			if self.default_rst is not None:
				rst_i = self.request(self.default_rst).i

			m = Module()
			ready = Signal()
			m.submodules += Instance(STARTUP_PRIMITIVE[self.family], o_EOS = ready)
			m.domains += ClockDomain('sync', reset_less = self.default_rst is None)
			if self.toolchain != 'Vivado':
				m.submodules += Instance('BUFGCE', i_CE = ready, i_I = clk_i, o_O = ClockSignal('sync'))
			elif self.family == 'series7':
				# Actually use BUFGCTRL configured as BUFGCE, since using BUFGCE causes
				# sim/synth mismatches with Vivado 2019.2, and the suggested workaround
				# (SIM_DEVICE parameter) breaks Vivado 2017.4.
				m.submodules += Instance(
					'BUFGCTRL',
					p_SIM_DEVICE = '7SERIES',
					i_I0         = clk_i,
					i_S0         = Const(1, 1),
					i_CE0        = ready,
					i_IGNORE0    = Const(0, 1),
					i_I1         = Const(1, 1),
					i_S1         = Const(0, 1),
					i_CE1        = Const(0, 1),
					i_IGNORE1    = Const(1, 1),
					o_O          = ClockSignal('sync')
				)
			else:
				m.submodules += Instance(
					'BUFGCE',
					p_SIM_DEVICE = 'ULTRASCALE',
					i_CE = ready,
					i_I = clk_i,
					o_O = ClockSignal('sync')
				)
			if self.default_rst is not None:
				m.submodules.reset_sync = ResetSynchronizer(rst_i, domain = 'sync')
			return m

	def add_clock_constraint(self, clock: Signal, frequency: int | float) -> None:
		super().add_clock_constraint(clock, frequency)
		clock.attrs['keep'] = 'TRUE'

	def _get_xdr_buffer(
		self, m: Module, pin: Pin, iostd, *, i_invert: bool = False, o_invert: bool = False
	) -> tuple[Signal | None, Signal | None, Signal | None]:
		XFDDR_FAMILIES = {
			'virtex2',
			'virtex2p',
			'spartan3',
		}
		XDDR2_FAMILIES = {
			'spartan3e',
			'spartan3a',
			'spartan3adsp',
			'spartan6',
		}
		XDDR_FAMILIES = {
			'virtex4',
			'virtex5',
			'virtex6',
			'series7',
		}
		XDDRE1_FAMILIES = {
			'ultrascale',
			'ultrascaleplus',
		}

		def get_iob_dff(clk: Signal, d: Signal, q: Signal) -> None:
			# SDR I/O is performed by packing a flip-flop into the pad IOB.
			for bit in range(len(q)):
				m.submodules += Instance(
					'FDCE',
					a_IOB = 'TRUE',
					i_C = clk,
					i_CE = Const(1),
					i_CLR = Const(0),
					i_D = d[bit],
					o_Q = q[bit]
				)

		def get_dff(clk: Signal, d: Signal, q: Signal) -> None:
			for bit in range(len(q)):
				m.submodules += Instance(
					'FDCE',
					i_C = clk,
					i_CE = Const(1),
					i_CLR = Const(0),
					i_D = d[bit],
					o_Q = q[bit]
				)

		def get_ifddr(clk: Signal, io: Signal, q0: Signal, q1: Signal) -> None:
			if self.family not in XFDDR_FAMILIES:
				raise ValueError(f'Family {self.family} is not IFDDR capable')

			for bit in range(len(q0)):
				m.submodules += Instance(
					'IFDDRCPE',
					i_C0 = clk,
					i_C1 = ~clk,
					i_CE = Const(1),
					i_CLR = Const(0),
					i_PRE = Const(0),
					i_D = io[bit],
					o_Q0 = q0[bit],
					o_Q1 = q1[bit]
				)

		def get_iddr2(clk: Signal, d: Signal, q0: Signal, q1: Signal, alignment) -> None:
			if self.family not in XDDR2_FAMILIES:
				raise ValueError(f'Family {self.family} is not IDDR2 capable')

			for bit in range(len(q0)):
				m.submodules += Instance(
					'IDDR2',
					p_DDR_ALIGNMENT = alignment,
					p_SRTYPE = 'ASYNC',
					p_INIT_Q0 = Const(0, 1),
					p_INIT_Q1 = Const(0, 1),
					i_C0 = clk,
					i_C1 = ~clk,
					i_CE = Const(1),
					i_S = Const(0),
					i_R = Const(0),
					i_D = d[bit],
					o_Q0 = q0[bit],
					o_Q1 = q1[bit]
				)

		def get_iddr(clk: Signal, d: Signal, q1: Signal, q2: Signal) -> None:
			if self.family not in XDDR_FAMILIES or self.family not in XDDRE1_FAMILIES:
				raise ValueError(f'Family {self.family} is not IDDR capable')

			for bit in range(len(q1)):
				if self.family in XDDR_FAMILIES:
					m.submodules += Instance(
						'IDDR',
						p_DDR_CLK_EDGE = 'SAME_EDGE_PIPELINED',
						p_SRTYPE = 'ASYNC',
						p_INIT_Q1 = Const(0, 1),
						p_INIT_Q2 = Const(0, 1),
						i_C = clk,
						i_CE = Const(1),
						i_S = Const(0),
						i_R = Const(0),
						i_D = d[bit],
						o_Q1 = q1[bit],
						o_Q2 = q2[bit]
					)
				else:
					m.submodules += Instance(
						'IDDRE1',
						p_DDR_CLK_EDGE = 'SAME_EDGE_PIPELINED',
						p_IS_C_INVERTED = Const(0, 1),
						p_IS_CB_INVERTED = Const(1, 1),
						i_C = clk,
						i_CB = clk,
						i_R = Const(0),
						i_D = d[bit],
						o_Q1 = q1[bit],
						o_Q2 = q2[bit]
					)

		def get_fddr(clk: Signal, d0: Signal, d1: Signal, q: Signal) -> None:
			for bit in range(len(q)):
				if self.family in XFDDR_FAMILIES:
					m.submodules += Instance(
						'FDDRCPE',
						i_C0 = clk,
						i_C1 = ~clk,
						i_CE = Const(1),
						i_PRE = Const(0),
						i_CLR = Const(0),
						i_D0 = d0[bit],
						i_D1 = d1[bit],
						o_Q = q[bit]
					)
				else:
					m.submodules += Instance(
						'ODDR2',
						p_DDR_ALIGNMENT = 'NONE',
						p_SRTYPE = 'ASYNC',
						p_INIT = Const(0, 1),
						i_C0 = clk,
						i_C1 = ~clk,
						i_CE = Const(1),
						i_S = Const(0),
						i_R = Const(0),
						i_D0 = d0[bit],
						i_D1 = d1[bit],
						o_Q = q[bit]
					)

		def get_oddr(clk: Signal, d1: Signal, d2: Signal, q: Signal) -> None:
			for bit in range(len(q)):
				if self.family in XDDR2_FAMILIES:
					m.submodules += Instance(
						'ODDR2',
						p_DDR_ALIGNMENT = 'C0',
						p_SRTYPE = 'ASYNC',
						p_INIT = Const(0, 1),
						i_C0 = clk,
						i_C1 = ~clk,
						i_CE = Const(1),
						i_S = Const(0),
						i_R = Const(0),
						i_D0 = d1[bit],
						i_D1 = d2[bit],
						o_Q = q[bit]
					)
				elif self.family in XDDR_FAMILIES:
					m.submodules += Instance(
						'ODDR',
						p_DDR_CLK_EDGE = 'SAME_EDGE',
						p_SRTYPE = 'ASYNC',
						p_INIT = Const(0, 1),
						i_C = clk,
						i_CE = Const(1),
						i_S = Const(0),
						i_R = Const(0),
						i_D1 = d1[bit],
						i_D2 = d2[bit],
						o_Q = q[bit]
					)
				elif self.family in XDDRE1_FAMILIES:
					m.submodules += Instance(
						'ODDRE1',
						p_SRVAL = Const(0, 1),
						i_C = clk,
						i_SR = Const(0),
						i_D1 = d1[bit],
						i_D2 = d2[bit],
						o_Q = q[bit]
					)

		def get_ineg(y: Signal, invert: bool) -> Signal:
			if invert:
				a = Signal.like(y, name_suffix = '_n')
				m.d.comb += y.eq(~a)
				return a
			else:
				return y

		def get_oneg(a: Signal, invert: bool) -> Signal:
			if invert:
				y = Signal.like(a, name_suffix = '_n')
				m.d.comb += y.eq(~a)
				return y
			else:
				return a

		if 'i' in pin.dir:
			if pin.xdr < 2:
				pin_i  = get_ineg(pin.i,  i_invert)
			elif pin.xdr == 2:
				pin_i0 = get_ineg(pin.i0, i_invert)
				pin_i1 = get_ineg(pin.i1, i_invert)
		if 'o' in pin.dir:
			if pin.xdr < 2:
				pin_o  = get_oneg(pin.o,  o_invert)
			elif pin.xdr == 2:
				pin_o0 = get_oneg(pin.o0, o_invert)
				pin_o1 = get_oneg(pin.o1, o_invert)

		i = o = t = None
		if 'i' in pin.dir:
			i = Signal(pin.width, name = f'{pin.name}_xdr_i')
		if 'o' in pin.dir:
			o = Signal(pin.width, name = f'{pin.name}_xdr_o')
		if pin.dir in ('oe', 'io'):
			t = Signal(1,         name = f'{pin.name}_xdr_t')

		if pin.xdr == 0:
			if 'i' in pin.dir:
				i = pin_i
			if 'o' in pin.dir:
				o = pin_o
			if pin.dir in ('oe', 'io'):
				t = ~pin.oe
		elif pin.xdr == 1:
			if 'i' in pin.dir:
				get_iob_dff(pin.i_clk, i, pin_i)
			if 'o' in pin.dir:
				get_iob_dff(pin.o_clk, pin_o, o)
			if pin.dir in ('oe', 'io'):
				get_iob_dff(pin.o_clk, ~pin.oe, t)
		elif pin.xdr == 2:
			# On Spartan 3E/3A, the situation with DDR registers is messy: while the hardware
			# supports same-edge alignment, it does so by borrowing the resources of the other
			# pin in the differential pair (if any).  Since we cannot be sure if the other pin
			# is actually unused (or if the pin is even part of a differential pair in the first
			# place), we only use the hardware alignment feature in two cases:
			#
			# - differential inputs (since the other pin's input registers will be unused)
			# - true differential outputs (since they use only one pin's output registers,
			#   as opposed to pseudo-differential outputs that use both)
			TRUE_DIFF_S3EA = {
				'LVDS_33', 'LVDS_25',
				'MINI_LVDS_33', 'MINI_LVDS_25',
				'RSDS_33', 'RSDS_25',
				'PPDS_33', 'PPDS_25',
				'TMDS_33',
			}
			DIFF_S3EA = TRUE_DIFF_S3EA | {
				'DIFF_HSTL_I',
				'DIFF_HSTL_III',
				'DIFF_HSTL_I_18',
				'DIFF_HSTL_II_18',
				'DIFF_HSTL_III_18',
				'DIFF_SSTL3_I',
				'DIFF_SSTL3_II',
				'DIFF_SSTL2_I',
				'DIFF_SSTL2_II',
				'DIFF_SSTL18_I',
				'DIFF_SSTL18_II',
				'BLVDS_25',
			}
			if 'i' in pin.dir:
				if self.family in XFDDR_FAMILIES:
					# First-generation input DDR register: basically just two FFs with opposite
					# clocks. Add a register on both outputs, so that they enter fabric on
					# the same clock edge, adding one cycle of latency.
					i0_ff = Signal.like(pin_i0, name_suffix = '_ff')
					i1_ff = Signal.like(pin_i1, name_suffix = '_ff')
					get_dff(pin.i_clk, i0_ff, pin_i0)
					get_dff(pin.i_clk, i1_ff, pin_i1)
					get_iob_dff(pin.i_clk, i, i0_ff)
					get_iob_dff(~pin.i_clk, i, i1_ff)
				elif self.family in XDDR2_FAMILIES:
					if self.family == 'spartan6' or iostd in DIFF_S3EA:
						# Second-generation input DDR register: hw realigns i1 to positive clock edge,
						# but also misaligns it with i0 input.  Re-register first input before it
						# enters fabric. This allows both inputs to enter fabric on the same clock
						# edge, and adds one cycle of latency.
						i0_ff = Signal.like(pin_i0, name_suffix = '_ff')
						get_dff(pin.i_clk, i0_ff, pin_i0)
						get_iddr2(pin.i_clk, i, i0_ff, pin_i1, 'C0')
					else:
						# No extra register available for hw alignment, use extra registers.
						i0_ff = Signal.like(pin_i0, name_suffix = '_ff')
						i1_ff = Signal.like(pin_i1, name_suffix = '_ff')
						get_dff(pin.i_clk, i0_ff, pin_i0)
						get_dff(pin.i_clk, i1_ff, pin_i1)
						get_iddr2(pin.i_clk, i, i0_ff, i1_ff, "NONE")
				else:
					# Third-generation input DDR register: does all of the above on its own.
					get_iddr(pin.i_clk, i, pin_i0, pin_i1)
			if "o" in pin.dir:
				if self.family in XFDDR_FAMILIES or self.family == 'spartan3e' or (
					self.family.startswith("spartan3a") and iostd not in TRUE_DIFF_S3EA
				):
					# For this generation, we need to realign o1 input ourselves.
					o1_ff = Signal.like(pin_o1, name_suffix = '_ff')
					get_dff(pin.o_clk, pin_o1, o1_ff)
					get_fddr(pin.o_clk, pin_o0, o1_ff, o)
				else:
					get_oddr(pin.o_clk, pin_o0, pin_o1, o)
			if pin.dir in ('oe', 'io'):
				if self.family == 'spartan6':
					get_oddr(pin.o_clk, ~pin.oe, ~pin.oe, t)
				else:
					get_iob_dff(pin.o_clk, ~pin.oe, t)
		else:
			raise ValueError(f'Invalid gearing {pin.xdr} for pin {pin.name}, must be one of, 0, 1, or 2')

		return (i, o, t)

	def _get_valid_xdrs(self) -> tuple[Literal[0], Literal[1]] | tuple[Literal[0], Literal[1], Literal[2]]:
		if self.family in { 'virtex', 'virtexe' }:
			return (0, 1)
		else:
			return (0, 1, 2)

	def get_input(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		self._check_feature(
			'single-ended input', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD'), i_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'IBUF',
				i_I = port.io[bit],
				o_O = i[bit]
			)
		return m

	def get_output(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		self._check_feature(
			'single-ended output', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD'), o_invert = invert)
		if self.toolchain != 'Symbiflow':
			for bit in range(pin.width):
				m.submodules[f'{pin.name}_{bit}'] = Instance(
					'OBUF',
					i_I = o[bit],
					o_O = port.io[bit]
				)
		else:
			m.d.comb += port.eq(self._invert_if(invert, o))
		return m

	def get_tristate(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_tristate(pin, port, attrs, invert)

		self._check_feature(
			'single-ended tristate', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD'), o_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'OBUFT',
				i_T = t,
				i_I = o[bit],
				o_O = port.io[bit]
			)
		return m

	def get_input_output(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_input_output(pin, port, attrs, invert)

		self._check_feature(
			'single-ended input/output', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD'), i_invert = invert, o_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'IOBUF',
				i_T = t,
				i_I = o[bit],
				o_O = i[bit],
				io_IO = port.io[bit]
			)
		return m

	def get_diff_input(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_diff_input(pin, port, attrs, invert)

		self._check_feature(
			'differential input', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD', 'LVDS_25'), i_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'IBUFDS',
				i_I = port.p[bit],
				i_IB = port.n[bit],
				o_O = i[bit]
			)
		return m

	def get_diff_output(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_diff_output(pin, port, attrs, invert)

		self._check_feature(
			'differential output', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD', 'LVDS_25'), o_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'OBUFDS',
				i_I = o[bit],
				o_O = port.p[bit],
				o_OB = port.n[bit]
			)
		return m

	def get_diff_tristate(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_diff_tristate(pin, port, attrs, invert)

		self._check_feature(
			'differential tristate', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD', 'LVDS_25'), o_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'OBUFTDS',
				i_T = t,
				i_I = o[bit],
				o_O = port.p[bit],
				o_OB = port.n[bit]
			)
		return m

	def get_diff_input_output(self, pin: Pin, port: Record, attrs: Attrs, invert: bool) -> Module:
		if self.toolchain == 'Symbiflow':
			return super().get_diff_input_output(pin, port, attrs, invert)

		self._check_feature(
			'differential input/output', pin, attrs, valid_xdrs = self._get_valid_xdrs(), valid_attrs = True
		)

		m = Module()
		i, o, t = self._get_xdr_buffer(m, pin, attrs.get('IOSTANDARD', 'LVDS_25'), i_invert = invert, o_invert = invert)
		for bit in range(pin.width):
			m.submodules[f'{pin.name}_{bit}'] = Instance(
				'IOBUFDS',
				i_T = t,
				i_I = o[bit],
				o_O = i[bit],
				io_IO = port.p[bit],
				io_IOB = port.n[bit]
			)
		return m

	# The synchronizer implementations below apply two separate but related timing constraints.
	#
	# First, the ASYNC_REG attribute prevents inference of shift registers from synchronizer FFs,
	# and constraints the FFs to be placed as close as possible, ideally in one CLB. This attribute
	# only affects the synchronizer FFs themselves.
	#
	# Second, for Vivado only, the torii.vivado.false_path or torii.vivado.max_delay attribute
	# affects the path into the synchronizer. If maximum input delay is specified, a datapath-only
	# maximum delay constraint is applied, limiting routing delay (and therefore skew) at
	# the synchronizer input.  Otherwise, a false path constraint is used to omit the input path
	# from the timing analysis.

	def get_ff_sync(self, ff_sync) -> Module:
		m = Module()
		flops = [
			Signal(
				ff_sync.i.shape(), name = f'stage{index}',
				reset = ff_sync._reset, reset_less = ff_sync._reset_less,
				attrs = { 'ASYNC_REG': 'TRUE' }
			)
			for index in range(ff_sync._stages)
		]
		if self.toolchain == 'Vivado':
			if ff_sync._max_input_delay is None:
				flops[0].attrs['torii.vivado.false_path'] = 'TRUE'
			else:
				flops[0].attrs['torii.vivado.max_delay'] = str(ff_sync._max_input_delay * 1e9)
		elif ff_sync._max_input_delay is not None:
			raise NotImplementedError(
				f'Platform \'{type(self).__name__}\' does not support constraining input delay for FFSynchronizer'
			)
		for i, o in zip((ff_sync.i, *flops), flops):
			m.d[ff_sync._o_domain] += o.eq(i)
		m.d.comb += ff_sync.o.eq(flops[-1])
		return m

	def get_async_ff_sync(self, async_ff_sync) -> Module:
		m = Module()
		m.domains += ClockDomain('async_ff', async_reset = True, local = True)
		flops = [
			Signal(1, name = f'stage{index}', reset = 1, attrs = { 'ASYNC_REG': 'TRUE' })
			for index in range(async_ff_sync._stages)
		]
		if self.toolchain == 'Vivado':
			if async_ff_sync._max_input_delay is None:
				flops[0].attrs['torii.vivado.false_path'] = 'TRUE'
			else:
				flops[0].attrs['torii.vivado.max_delay'] = str(async_ff_sync._max_input_delay * 1e9)
		elif async_ff_sync._max_input_delay is not None:
			raise NotImplementedError(
				f'Platform \'{type(self).__name__}\' does not support constraining input delay for AsyncFFSynchronizer'
			)

		for i, o in zip((0, *flops), flops):
			m.d.async_ff += o.eq(i)

		if async_ff_sync._edge == 'pos':
			m.d.comb += ResetSignal('async_ff').eq(async_ff_sync.i)
		else:
			m.d.comb += ResetSignal('async_ff').eq(~async_ff_sync.i)

		m.d.comb += [
			ClockSignal('async_ff').eq(ClockSignal(async_ff_sync._o_domain)),
			async_ff_sync.o.eq(flops[-1])
		]

		return m
