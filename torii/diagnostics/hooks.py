# SPDX-License-Identifier: BSD-2-Clause

'''

This module contains the internal implementation of the ``showwarning`` hook that Torii can install
in order to produce pretty and/or machine consumable warning messages.

'''

# TODO(aki): Document once the docs refactor is merged in

import sys
import warnings
from linecache     import getline, getlines
from os            import getenv
from pathlib       import Path
from textwrap      import wrap
from sys           import stderr, stdout
from types         import TracebackType
from typing        import Final, TextIO, TypedDict

from rich          import get_console
from rich.console  import Console
from rich.padding  import Padding
from rich.panel    import Panel
from rich.syntax   import Syntax

from ..diagnostics import ToriiSyntaxError
from ..hdl._unused import MustUse

# Create a reference to the handlers that are installed prior to us loading
_WARN_HANDLER_RESTORE = warnings.showwarning
_EXCEPTHOOK_RESTORE   = sys.excepthook

# The Torii modules we want to explicitly force warnings on for
_TORII_MODULES = (
	'torii',
	'torii_boards',
	'torii_usb',
	'torii_ila',
)

# Defaults for warning rendering
DEFAULT_USE_FANCY: Final[bool]    = True
DEFAULT_FANCY_CONTEXT: Final[int] = 5
DEFAULT_FANCY_WIDTH: Final[int]   = 8192 # Big so we will clamp to term width by default
DEFAULT_STRIP_PATH: Final[bool]   = False

class WarningRenderingOptions(TypedDict):
	use_fancy: bool
	fancy_context: int
	fancy_width: int
	strip_path: bool

def _populate_options() -> WarningRenderingOptions:
	use_fancy = not getenv('TORII_DIAGNOSTICS_NOFANCY', False)

	try:
		if (val := int(getenv('TORII_DIAGNOSTICS_CONTEXT', ''))) > 0:
			fancy_context = val
		else:
			fancy_context = DEFAULT_FANCY_CONTEXT
	except Exception:
		fancy_context = DEFAULT_FANCY_CONTEXT

	try:
		if (val := int(getenv('TORII_DIAGNOSTICS_WIDTH', ''))) > 0:
			fancy_width = val
		else:
			fancy_width = DEFAULT_FANCY_WIDTH
	except Exception:
		fancy_width = DEFAULT_FANCY_WIDTH

	strip_path = bool(getenv('TORII_DIAGNOSTICS_STRIP', DEFAULT_STRIP_PATH))

	return WarningRenderingOptions(
		use_fancy     = use_fancy,
		fancy_context = fancy_context,
		fancy_width   = fancy_width,
		strip_path    = strip_path
	)

# Options for how we want to render our warnings
_WARNING_RENDERING_OPTIONS = _populate_options()

def _get_console(output_stream: TextIO | None) -> Console:
	'''
	Get the appropriate :py:mod:`rich` :py:class:`Console <rich.console.Console>` to use
	for rendering our warning output.

	Parameters
	----------
	output_stream : typing.TextIO | None
		The stream to render our Console to.

		If it is ``None`` or :py:class:`sys.stdout` then the default Rich
		:py:class:`Console <rich.console.Console>` is used.
	'''
	if output_stream is None or output_stream == stdout:
		return get_console()
	else:
		return Console(file = output_stream)

# NOTE(aki): I don't like the nocov here but it's *really* hard to test this
def _render_fancy(cons: Console, filename: str, lineno: int, border_style: str, width: int) -> bool: # :nocov:
	'''
	Render the fancy syntax-highlighted code context for the warning display.

	Parameters
	----------
	cons : rich.console.Console
		The Console to render to.

	filename : str
		The name of the file the warning occurred in.

	lineno : int
		The line of ``filename`` the warning was raised from.

	border_style : str
		The border style of the panel frame.

	Returns
	-------
	bool
		True if there was code to render, otherwise False
	'''

	# Ensure we have *some* code to actually render
	if (code := ''.join(getlines(filename))):
		# Set up the context window for the code display (±N lines around lineno)
		context = (
			lineno - _WARNING_RENDERING_OPTIONS['fancy_context'],
			lineno + _WARNING_RENDERING_OPTIONS['fancy_context']
		)

		# Render the code into a syntax highlighted block
		code_render = Syntax(
			code, 'python',
			theme = Syntax.get_theme('ansi_light'),
			line_numbers = True,
			line_range = context,
			highlight_lines = { lineno },
			code_width = width,
			indent_guides = False,
			word_wrap = True,
			dedent = False,
		)

		# Fixup the filename if we're stripping the file path
		if _WARNING_RENDERING_OPTIONS['strip_path']:
			filename = Path(filename).name

		render_title = f'[cyan]{filename}[/][white]:[/][magenta]{lineno}[/]'

		# If the output console is a terminal, then stick it in a titled box
		if cons.is_terminal:
			# Stuff the code inside a fancy panel
			display_panel = Panel.fit(
				code_render, title = render_title, border_style = border_style
			)

			# Render the code a little bit off the side of the terminal
			cons.print(Padding(display_panel, pad = (0, 1, 0, 1)))
		else:
			cons.print(render_title)
			cons.print(code_render)
		return True

	return False

def _render_diagnostic( # :nocov:
	cons: Console, message: str, category: type[Warning | BaseException], filename: str, lineno: int,
	accent_color: str, line: str | None = None, notes: list[str] | None = None
) -> None:

	# If we want to show the source lines, make sure we can, and it's not the REPL
	show_source = _WARNING_RENDERING_OPTIONS['use_fancy'] and filename != 'sys'

	# Clamp the width of the code block to either our wanted width or terminal width
	# and subtract padding for the panel render
	width = min(cons.width, _WARNING_RENDERING_OPTIONS['fancy_width']) - 4

	# Print out the diagnostic type/message
	cons.print(f' [{accent_color}]{category.__name__}[/][white]:[/] {message}')

	if show_source:
		show_source = _render_fancy(cons, filename, lineno, border_style = accent_color, width = width)
	else:
		# If the line we were given is None try to get it from the linecache
		if line is None:
			line = getline(filename, lineno)

		cons.print(f'{filename}:{lineno}: {line}')

	# If we have any notes to render, do so
	if notes is not None and len(notes) > 0:
		for (idx, note) in enumerate(notes):
			if len(note) + 12 > width - 1:
				note = '\n'.join(wrap(note, width - 8, subsequent_indent = '         '))
			cons.print(f' [cyan]=[/] [bold white]note:[/] {note}', overflow = 'ignore')

	# If we are showing the sources, give us some breathing room
	if show_source:
		cons.line()

# NOTE(aki): I don't like the nocov here but it's *really* hard to test this
def _warning_handler( # :nocov:
	message: Warning | str, category: type[Warning] | None, filename: str, lineno: int,
	output_file: TextIO | None = None, line: str | None = None
) -> None:
	'''
	The Torii warning handler.

	By default, this will render a stylized code block render of the context around where the warning
	was raised, this behavior can be controlled with the following environment variables:

	* ``TORII_DIAGNOSTICS_NOFANCY`` - Disables rendering of the code block, will simply print two lines giving
	the warning and the file and line number.
	* ``TORII_DIAGNOSTICS_CONTEXT`` - The number of lines above and below the line the warning to show in the
	render. Defaults to ``5``
	* ``TORII_DIAGNOSTICS_WIDTH`` - How wide to clamp the code render, will always clamp to terminal width if
	is smaller. Defaults to ``8192``
	* ``TORII_DIAGNOSTICS_STRIP`` - Strip the full file path from the warning render, instead only showing just
	the file name.

	On Python 3.11 and newer, :py:class:`Warning`'s can have optional notes attached to them via the
	:py:meth:`BaseException.add_note` function.

	If Torii is running on Python 3.11 or newer, and the raised :py:class:`Warning` has any attached notes
	they will be listed after the warning message and context display.

	Parameters
	----------
	message : Warning | str
		The :py:class:`Warning` instance or the warning message.

	category : type[Warning] | None
		The :py:class:`Warning` category if ``message`` is a string, otherwise None.

	filename: str
		The name of the file the warning was raised in.

	lineno: int
		The line of ``filename`` the warning was raised on.

	output_file: TextIO | None
		The output stream to write the warning message to.

		If ``None`` it defaults to :py:class:`sys.stdout`

	line : str | None
		The text of the line the warning was raised on.

		If ``None`` this is collected with the :py:mod:`linecache` module,
		using the provided ``filename`` and ``lineno``.
	'''

	notes: list[str] | None = None

	# Get the output console to write to
	cons = _get_console(output_file)

	# If `message` is a `Warning` itself, the category is ignored in favor of `message.__class__`
	# and the message is the stringified object
	if isinstance(message, Warning):
		category = message.__class__

		# If we are in Python 3.11 or newer, then we can have attached notes
		notes = getattr(message, '__notes__', None)
		message  = str(message)

	# If the category is `None`, then we need to just say it's a generic warning
	if category is None:
		category = Warning

	_render_diagnostic(cons, message, category, filename, lineno, 'yellow', line, notes)

def _excepthook(type: type[BaseException], value: BaseException, traceback: TracebackType | None) -> None:
	'''
	The Torii exception hook handler.

	By default, this will render a stylized code block render of the context around where the warning
	was raised, this behavior can be controlled with the following environment variables:

	* ``TORII_DIAGNOSTICS_NOFANCY`` - Disables rendering of the code block, will simply print two lines giving
	the warning and the file and line number.
	* ``TORII_DIAGNOSTICS_CONTEXT`` - The number of lines above and below the line the warning to show in the
	render. Defaults to ``5``
	* ``TORII_DIAGNOSTICS_WIDTH`` - How wide to clamp the code render, will always clamp to terminal width if
	is smaller. Defaults to ``8192``
	* ``TORII_DIAGNOSTICS_STRIP`` - Strip the full file path from the warning render, instead only showing just
	the file name.

	On Python 3.11 and newer, :py:class:`Warning`'s can have optional notes attached to them via the
	:py:meth:`BaseException.add_note` function.

	If Torii is running on Python 3.11 or newer, and the raised :py:class:`Warning` has any attached notes
	they will be listed after the warning message and context display.

	This also explicitly disables the `UnusedElaboratable` diagnostic as having those be emitted
	when the interpreter dies would just cause more harm than good.

	Parameters
	----------
	type: type[BaseException]
		The type of exception that was caught.

	value: BaseException
		The actual exception that was caught.

	traceback: TracebackType | None
		The traceback for the exception
	'''

	# We assume the interpreter crashed, snuff unused elaboratable warnings
	MustUse._MustUse__silence = True

	# If it's a Torii SyntaxError, then we should try to emit a diagnostic
	if isinstance(value, ToriiSyntaxError):
		filename = value.filename
		lineno = value.lineno
		line = value.text

		# If we don't have a filename and/or line number then there is very little we can do
		if filename is None or lineno is None:
			_EXCEPTHOOK_RESTORE(type, value, traceback)
			return

		cons = _get_console(stderr)
		_render_diagnostic(cons, value.msg, type, filename, lineno, 'red', line, getattr(value, '__notes__', None))
	else:
		_EXCEPTHOOK_RESTORE(type, value, traceback)

def install_warning_handler(*, catch_all: bool = False) -> None:
	'''
	Replace the current :py:meth:`warnings.showwarning` handler with the Torii warning handler,
	saving the original so it can be restored when calling :py:meth:`remove_warning_handler`.

	If the environment variable ``TORII_DIAGNOSTICS_NOHANDLE`` is set, then this function has no effect
	and the current warning handler will remain installed.

	Note
	----
	If the ``catch_all`` parameter is not set, or set to ``False``, then this method will still force
	enable :py:class:`DeprecationWarning` and :py:class:`SyntaxWarning` warnings for a list of known
	Torii modules regardless.

	Parameters
	----------
	catch_all : bool
		Flush the Python warnings filters so all warnings are asserted.
	'''

	# If the environment is telling us to not handle the warnings don't,
	# or if the handler is already installed, don't re-install it.
	if getenv('TORII_DIAGNOSTICS_NOHANDLE') or warnings.showwarning == _warning_handler:
		return

	# Catch all warnings if requested, otherwise ensure torii's warnings get emitted at least
	if catch_all:
		warnings.resetwarnings()
	else:
		for torii_mod in _TORII_MODULES:
			warnings.filterwarnings('always', category = DeprecationWarning, module = torii_mod)
			warnings.filterwarnings('always', category = SyntaxWarning, module = torii_mod)

	# Store the handler we want to restore later on `remove_handler`
	global _WARN_HANDLER_RESTORE
	_WARN_HANDLER_RESTORE = warnings.showwarning

	# Install the new warning handler
	warnings.showwarning = _warning_handler

def remove_warning_handler() -> None:
	'''
	Restore the original :py:meth:`warnings.showwarning` handler that was present before the
	call to :py:meth:`install_warning_handler`.
	'''

	# If we didn't install the handler, we might restore incorrectly, so don't bother
	if getenv('TORII_DIAGNOSTICS_NOHANDLE'):
		return

	# Restore the warning handler
	warnings.showwarning = _WARN_HANDLER_RESTORE

def install_excepthook() -> None:
	'''
	Replace the current :py:meth:`sys.excepthook` handler with the Torii excepthook handler,
	saving the original so it can be restored when calling :py:meth:`remove_excepthook`.
	'''

	# Store the pre-existing handler
	global _EXCEPTHOOK_RESTORE
	_EXCEPTHOOK_RESTORE = sys.excepthook

	# Install the excepthook
	sys.excepthook = _excepthook

def remove_excepthook() -> None:
	'''
	Restore the original :py:meth:`sys.excepthook` handler that was present before the
	call to :py:meth:`install_excepthook`.
	'''

	sys.excepthook = _EXCEPTHOOK_RESTORE

def install_handlers(*, catch_all: bool = False) -> None:
	'''
	Replace the current :py:meth:`sys.excepthook` and :py:meth:`warnings.showwarning` handlers with the
	Torii handlers, saving the originals so they can be restored when calling :py:meth:`remove_handlers`.

	Note
	----
	If the ``catch_all`` parameter is not set, or set to ``False``, then this method will still force
	enable :py:class:`DeprecationWarning` and :py:class:`SyntaxWarning` warnings for a list of known
	Torii modules regardless.

	Parameters
	----------
	catch_all : bool
		Flush the Python warnings filters so all warnings are asserted.
	'''

	install_warning_handler(catch_all = catch_all)
	install_excepthook()

def remove_handlers() -> None:
	'''
	Restore the original :py:meth:`sys.excepthook` and :py:meth:`warnings.showwarning` handlers that were
	present before the call to :py:meth:`install_handlers`.
	'''

	remove_warning_handler()
	remove_excepthook()
