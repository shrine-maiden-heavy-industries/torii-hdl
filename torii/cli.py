# SPDX-License-Identifier: BSD-2-Clause
import logging    as log
from argparse     import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace

from rich         import traceback, print
from rich.logging import RichHandler
from rich.prompt  import IntPrompt, Prompt, Confirm
from rich.columns import Columns

__all__ = (
	'main',
)

def setup_logging(args: Namespace = None) -> None:
	'''
	Initialize logging subscriber

	Set up the built-in rich based logging subscriber, and force it
	to be the one at runtime in case there is already one set up.

	Parameters
	----------
	args : argparse.Namespace
		Any command line arguments passed.

	'''

	level = log.INFO
	if args is not None and args.verbose:
		level = log.DEBUG

	log.basicConfig(
		force    = True,
		format   = '%(message)s',
		datefmt  = '[%X]',
		level    = level,
		handlers = [
			RichHandler(rich_tracebacks = True, show_path = False)
		]
	)


def torii_collect_boards():
	import importlib
	import inspect
	import pkgutil

	from .build.plat import Platform, TemplatedPlatform

	available_boards = {}

	def _is_board(member) -> bool:
		name: str = member[0]
		obj: object = member[1]

		is_valid_class = not name.startswith('_') and inspect.isclass(obj)
		is_valid_platform = is_valid_class and issubclass(obj, (Platform, TemplatedPlatform))

		return is_valid_platform and not isinstance(obj.pretty_name, property)

	if (spec := importlib.util.find_spec('torii_boards')) is not None:
		boards = importlib.util.module_from_spec(spec)

		for vendor_mod in filter(lambda m: m.name != 'test' and m.ispkg, pkgutil.iter_modules(boards.__path__)):
			vendor_mod_path = f'{boards.__path__[0]}/{vendor_mod.name}'
			vendor_boards = []

			for vendor_board in filter(lambda m: not m.ispkg, pkgutil.iter_modules([vendor_mod_path])):
				board_mod_name = f'torii_boards.{vendor_mod.name}.{vendor_board.name}'
				if (board_spec := importlib.util.find_spec(board_mod_name)) is not None:
					brd = importlib.util.module_from_spec(board_spec)
					board_spec.loader.exec_module(brd)

					for cname, cls in filter(_is_board, inspect.getmembers(brd)):
						vendor_boards.append({
							'package': board_mod_name,
							'class': cname,
							'name': cls.pretty_name,
							'desc': cls.description
						})

					del brd
				else:
					log.warning(f'Unable to reflect on {board_mod_name}')
			available_boards[vendor_mod.name] = vendor_boards
		del boards

	return available_boards


def torii_action_reg_new(parser: ArgumentParser):
	pass

def torii_action_run_new(args: Namespace) -> int:
	available_boards = torii_collect_boards()

	def _format_boards(boards):
		for idx, board in enumerate(boards):
			yield f'[bold cyan]{idx:>3}.[/] [magenta]{board["name"]:<20}[/]: [green]{board["desc"]}[/]'

	def _collect_details():
		while (prj_name := Prompt.ask('Project Name')) == '':
			print('[red]Name is required[/]')

		prj_board = None

		if len(available_boards.keys()) > 0:
			if Confirm.ask('Use Existing Board?', default = True):
				prj_vend = Prompt.ask('Board Vendor', choices = available_boards.keys())
				brds     = available_boards.get(prj_vend)
				brd_cnt  = len(brds) - 1
				brd_col  = Columns(_format_boards(brds), equal = True, expand = True)
				print(brd_col)

				while (sel := IntPrompt.ask(f'Board Definition (0-{brd_cnt})')) > brd_cnt:
					print(brd_col)
					print('[red]Invalid selection[/]')

				prj_board = brds[sel]
		else:
			print('[yellow]It appears that you don\'t have the [bold magenta]torii_boards[/] package installed[/]')

		prj_init_vcs = Confirm.ask('Initialize git repository?', default = True)

		return {
			'name': prj_name,
			'brd_vend': prj_vend,
			'board': prj_board,
			'vcs': prj_init_vcs,
		}

	def _print_prj(prj):
		name  = prj['name']
		board = prj['board']
		vcs   = prj['vcs']

		print('[bold cyan]Summary[/]')
		print(f'[magenta]{"Name":>20}[/]: [green]{name}[/]')
		if board is not None:
			print(f'[magenta]{"Board Name":>20}[/]: [green]{board["name"]}[/]')
			print(f'[magenta]{"Board Desc":>20}[/]: [green]{board["desc"]}[/]')
		else:
			print(f'[magenta]{"Existing Board":>20}[/]: [green]False[/]')
		print(f'[magenta]{"Initialize Git":>20}[/]: [green]{"Yes" if vcs else "No"}[/]')

	prj_info = _collect_details()
	_print_prj(prj_info)
	while not Confirm.ask('Does this look Correct?'):
		prj_info = _collect_details()
		_print_prj(prj_info)

	return 0

TORII_ACTIONS = {
	'new':  (torii_action_run_new, torii_action_reg_new, 'Create a new Torii project from a template'),
}

def main() -> int:
	traceback.install()
	try:
		setup_logging()

		parser = ArgumentParser(
			formatter_class = ArgumentDefaultsHelpFormatter,
			description     = 'Torii',
			prog            = 'torii'
		)

		parser.add_argument(
			'--verbose', '-v',
			action = 'store_true',
			help   = 'Enable verbose output'
		)

		action_parser = parser.add_subparsers(
			dest = 'action',
			required = True
		)

		for name, (_, reg, desc) in TORII_ACTIONS.items():
			p = action_parser.add_parser(
				name,
				help = desc,
			)

			reg(p)

		args = parser.parse_args()

		act = list(filter(lambda act: act[0] == args.action, TORII_ACTIONS.items()))[0]
		return act[1][0](args)

	except KeyboardInterrupt:
		pass
