# SPDX-License-Identifier: BSD-2-Clause

from opcode        import opname
from sys           import _getframe, implementation
from typing        import TYPE_CHECKING

from ..diagnostics import NameNotFound
from .._typing     import SrcLoc

__all__ = (
	'get_src_loc',
	'get_var_name',
)

_IS_PYPY = implementation.name == 'pypy'

_raise_exception = object()

def get_var_name(depth: int = 2, default: str | object = _raise_exception) -> str:
	'''
	Get the variable name from an assignment up the call stack.

	By default, the result will be the file and line number from the call
	frame directly above the on in which ``get_var_name`` is called.

	This means, that if ``get_var_name`` is called in the constructor of an object,
	then the return value will be the name of the assignment that was done when constructing
	the object.

	Example
	-------
	.. autolink-preface:: from torii.util.tracer import get_var_name
	.. code:: pycon

		>>> class Nya:
		... 	def __init__(self) -> None:
		... 		self.name = get_var_name()
		...
		>>> meow = Nya() # `meow.name` will be `meow`
		>>> meow.name
		'meow'

	Parameters
	----------
	depth: int
		The number frames up the stack to look for the name from the variable assignment.

	default: str | object
		The default name to use if we are unable to determine what it should have been.

	Important
	---------
	The default value of ``depth`` is set so that the assignment of the result of the current call frame
	will be used.

	Raises
	------
	NameNotFound
		When the value of ``default`` is not explicitly set and we are unable to determine the name.
	'''

	frame = _getframe(depth)
	code = frame.f_code
	call_index = frame.f_lasti
	while call_index > 0 and opname[code.co_code[call_index]] == 'CACHE':
		call_index -= 2
	while True:
		call_opc = opname[code.co_code[call_index]]
		if call_opc in ('EXTENDED_ARG',):
			call_index += 2
		else:
			break
	if call_opc not in (
		'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX', 'CALL_METHOD', 'CALL_METHOD_KW', 'CALL', 'CALL_KW'
	):
		if default is _raise_exception:
			raise NameNotFound
		else:
			if TYPE_CHECKING:
				assert isinstance(default, str)
			return default

	index = call_index + 2
	imm = 0
	while True:
		opc = opname[code.co_code[index]]
		if opc == 'EXTENDED_ARG':
			imm |= int(code.co_code[index + 1])
			imm <<= 8
			index += 2
		elif opc in ('STORE_NAME', 'STORE_ATTR'):
			imm |= int(code.co_code[index + 1])
			return code.co_names[imm]
		elif opc == 'STORE_FAST':
			imm |= int(code.co_code[index + 1])
			if _IS_PYPY:
				return code.co_varnames[imm]
			return code._varname_from_oparg(imm) # type: ignore
		elif opc == 'STORE_DEREF':
			imm |= int(code.co_code[index + 1])
			if _IS_PYPY:
				if imm < len(code.co_cellvars):
					return code.co_cellvars[imm]
				else:
					return code.co_freevars[imm - len(code.co_cellvars)]
			return code._varname_from_oparg(imm) # type: ignore
		elif opc in (
			'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_ATTR', 'LOAD_FAST', 'LOAD_FAST_BORROW',
			'LOAD_DEREF', 'DUP_TOP', 'BUILD_LIST', 'CACHE', 'COPY'
		):
			imm = 0
			index += 2
		else:
			if default is _raise_exception:
				raise NameNotFound
			else:
				if TYPE_CHECKING:
					assert isinstance(default, str)
				return default

def get_src_loc(src_loc_at: int = 0) -> SrcLoc:
	'''
	Get the file and line number from the given frame on the call stack.

	By default, the result will be the file and line number from the call
	frame directly above the on in which ``get_src_loc`` is called.

	This means, that if ``get_src_loc`` is called in the constructor of an object,
	then the location information returned will be of where that constructor
	was called.

	Parameters
	----------
	src_loc_at: int
		The frame above this call in which to get the file and line number from.

	Example
	-------
	.. autolink-preface:: from torii.util.tracer import get_src_loc
	.. code:: pycon

		>>> class Nya:
		... 	def __init__(self) -> None:
		... 		self.src = get_src_loc()
		...
		>>> meow = Nya() # `meow.src` will be this line
		>>> meow.src
		('<python-input-4>', 1)

	Returns
	-------
	SrcLoc
		The file name and line number of the given stack frame.
	'''

	# n-th  frame: get_src_loc()
	# n-1th frame: caller of get_src_loc() (usually constructor)
	# n-2th frame: caller of caller (usually user code)
	frame = _getframe(2 + src_loc_at)
	return (frame.f_code.co_filename, frame.f_lineno)
