#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause

from argparse import ArgumentParser
from pathlib  import Path
from sys      import stdout, stderr
from typing   import TypedDict, Literal, NamedTuple

from rich     import print
from rich     import traceback

try:
	import tree_sitter_verilog as tsvlog
	from tree_sitter           import Language, Parser, Node
except ImportError:
	print(
		'Please install the \'tree-sitter\' and \'tree-sitter-verilog\' packages to use this script',
		file = stderr
	)
	raise SystemExit(1)

class Width(NamedTuple):
	msb: int
	lsb: int

class ModuleParam(TypedDict):
	name: str
	width: Width | int | None
	default: int | float | str

class ModulePort(TypedDict):
	name: str
	direction: Literal['input', 'output']
	width: Width | int | None

class ModuleHeader(TypedDict):
	name: str
	params: list[ModuleParam]
	ports: list[ModulePort]

VLOG_LANG   = Language(tsvlog.language())
VLOG_PARSER = Parser(VLOG_LANG)

MODULE_QUERY = VLOG_LANG.query('''
	(module_declaration
		(module_header
			(simple_identifier) @module.name
		)
		(module_ansi_header)
	) @module
''')

PARAM_QUERY = VLOG_LANG.query('''
	(module_ansi_header
		(parameter_port_list
			(parameter_port_declaration
				(parameter_declaration
					("parameter")
					(data_type_or_implicit1
						(implicit_data_type1
							(packed_dimension
								("[")
								(constant_range
									(constant_expression) @param.msb
									(":")
									(constant_expression) @param.lsb
								) @param.range
								("]")
							) @param.data
						)
					)*
					(list_of_param_assignments
						(param_assignment
							(parameter_identifier
								(simple_identifier) @param.name
							)
							("=")
							(constant_param_expression
								(constant_mintypmax_expression
									(constant_expression) @param.expr
								)
							)
						)
					)
				)+
			)
		)
	)
''')

MOD_PORTS_QUERY = VLOG_LANG.query('''
	(module_ansi_header
		(list_of_port_declarations
			(ansi_port_declaration
				(net_port_header1
					(port_direction) @port.direction
					(net_port_type1
						(data_type_or_implicit1
							(implicit_data_type1
								(packed_dimension
									("[")
									(constant_range
										(constant_expression) @port.msb
										(":")
										(constant_expression) @port.lsb
									) @port.range
									("]")
								) @port.data
							)
						)
					)?
				)?
				(port_identifier
					(simple_identifier) @port.name
				)
			) @port
		)
	)
''')

def _parse_default(value: str) -> str | int | float:
	if value[0] == '"' and value[-1] == '"':
		return value.strip('"')
	# TODO(aki): Parse the other values
	return value

def _extract_str(node: Node | None, raw_src: bytes) -> str:
	if node is None:
		return ''

	return raw_src[
		node.start_byte:node.end_byte
	].decode('utf8')

def _extract_params(matches: list[tuple[int, dict[str, list[Node]]]], raw_src: bytes) -> list[ModuleParam]:
	if len(matches) == 0:
		return []

	found: list[ModuleParam] = []

	for (_, nodes) in matches:
		name    = _extract_str(nodes.get('param.name', [None])[0], raw_src)
		default = _extract_str(nodes.get('param.expr', [None])[0], raw_src)
		msb     = _extract_str(nodes.get('param.msb',  [None])[0], raw_src)
		lsb     = _extract_str(nodes.get('param.lsb',  [None])[0], raw_src)

		if msb == '' and lsb == '':
			width = 1
		else:
			width = Width( int(msb), int(lsb) )

		found.append({
			'name': name,
			'default': _parse_default(default),
			'width': width
		})

	return found

def _extract_ports(matches: list[tuple[int, dict[str, list[Node]]]], raw_src: bytes) -> list[ModulePort]:
	if len(matches) == 0:
		return []

	found: list[ModulePort] = []

	for (_, nodes) in matches:
		name      = _extract_str(nodes.get('port.name',      [None])[0], raw_src)
		direction = _extract_str(nodes.get('port.direction', [None])[0], raw_src)
		msb       = _extract_str(nodes.get('port.msb',       [None])[0], raw_src)
		lsb       = _extract_str(nodes.get('port.lsb',       [None])[0], raw_src)

		# In the case the direction is not specified use the one of the previous port
		if direction == '':
			direction = found[-1]['direction']

		if msb == '' and lsb == '':
			width = 1
		else:
			width = Width( int(msb), int(lsb) )

		found.append({
			'name': name,
			'direction': direction,
			'width': width
		})

	return found

def _extract_modules(matches: list[tuple[int, dict[str, list[Node]]]], raw_src: bytes) -> list[ModuleHeader]:
	if len(matches) == 0:
		return []

	found: list[ModuleHeader] = []

	for (_, nodes) in matches:
		name   = _extract_str(nodes.get('module.name', [None])[0], raw_src)
		module = nodes.get('module', [None])[0]
		assert module is not None
		params = _extract_params(PARAM_QUERY.matches(module), raw_src)
		ports  = _extract_ports(MOD_PORTS_QUERY.matches(module), raw_src)

		found.append({
			'name': name,
			'params': params,
			'ports': ports
		})

	return found

def _generate_instance(module: ModuleHeader, output):
	mod_name = module["name"]

	output.write(f'# {mod_name}\n')

	port_padding = len(max(module['ports'], key = lambda k: len(k['name']))['name'])
	for port in module['ports']:
		if port['direction'] == 'output':
			width = port['width']
			if isinstance(width, Width):
				width = width.msb
			output.write(f'{mod_name}_{port["name"].ljust(port_padding, " ")} = Signal({width}) # TODO\n')

	output.write('\n')
	output.write(f'{mod_name} = Instance(\n')
	output.write(f'\t\'{mod_name}\',\n')

	if len(module['params']) > 0:
		padding = len(max(module['params'], key = lambda k: len(k['name']))['name'])
		output.write( '\t# Module Parameters\n')
		for param in module['params']:
			output.write(f'\tp_{param["name"].ljust(padding, " ")} = {param["default"]},\n')

	output.write( '\t# Module Ports\n')
	for port in module['ports']:
		if port['direction'] == 'input':
			output.write(f'\ti_{port["name"].ljust(port_padding, " ")} = Const(0), # TODO\n')
		elif port['direction'] == 'output':
			output.write(f'\to_{port["name"].ljust(port_padding, " ")} = {mod_name}_{port["name"]}, # TODO\n')

	output.write(')\n\n')

def main() -> int:
	traceback.install()

	parser = ArgumentParser(
		prog        = 'vlog2inst',
		description = 'Convert a verilog module definition into a Torii instance'
	)

	parser.add_argument(
		'input',
		help = 'The input verilog file to parse'
	)

	parser.add_argument(
		'output',
		default = '-',
		help    = 'The output file for the Torii instance, or \'-\' for stdout'
	)

	args = parser.parse_args()

	vlog_file = Path(args.input).resolve()
	if not vlog_file.exists():
		print(
			f'The input file \'{vlog_file}\' does not exit, aborting.',
			file = stderr
		)
		return 1

	out_file: str = args.output
	if out_file == '-':
		output = stdout
	else:
		output = Path(out_file).resolve().open('w')

	with vlog_file.open('rb') as src:
		raw_src = src.read(None)
		tree = VLOG_PARSER.parse(raw_src)

	modules = _extract_modules(MODULE_QUERY.matches(tree.root_node), raw_src)

	print(f'Found {len(modules)} modules:', file = stderr)
	output.write('# This file was automatically generated by vlog2inst\n')
	for module in modules:
		_generate_instance(module, output)

	if out_file != '-':
		output.close()

	return 0


if __name__ == '__main__':
	raise SystemExit(main())
