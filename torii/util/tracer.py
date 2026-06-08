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

def was_yielded(*, frame_loc_at: int = 0) -> bool:
	'''
	Attempt to determine if the caller for this method was used in a generator context.

	Warning
	-------
	This place is not a place of honor, no highly esteemed deed is commemorated here,
	nothing valued is here.

	The danger is still present, in your time, as it was in ours.

	The form of the danger is implementation details.
	'''

	frame = _getframe(2 + frame_loc_at)
	code = frame.f_code.co_code
	call_index = frame.f_lasti

	# Align  our last instruction index to find the `CALL` that should have been for us
	while call_index > 0 and opname[code[call_index]] == 'CACHE':
		call_index -= 2

	# Skip passed extended args
	while True:
		call_opc = opname[code[call_index]]
		if call_index in ('EXTENDED_ARG',):
			call_index += 2
		else:
			break

	# If the opcode we landed on is /not/ a `CALL`, then, for one, how did we end up here, but two
	# just assume we've not been called from a `yield`/`yield from`
	if call_opc not in (
		'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX', 'CALL_METHOD', 'CALL_METHOD_KW',
		'CALL', 'CALL_KW'
	):
		return False

	# Advance passed the `CALL` op
	index = call_index + 2

	# If we found the call site for and we have a name due to an assignment, check to see if the
	# result of this function is yielded at any point in time in the frame.
	if (name := get_var_name(depth = 3 + frame_loc_at, default = '')) != '':
		frame_code = frame.f_code

		# Check to see where the result of the call is stored so we can figure out which load ops
		# we need to check for
		if name in frame_code.co_names:
			load_opcodes = ('LOAD_NAME', 'LOAD_ATTR',)
			name_table = frame_code.co_names
		elif name in frame_code.co_varnames:
			load_opcodes = ('LOAD_FAST', 'LOAD_FAST_BORROW', )
			name_table = frame_code.co_varnames
		elif name in frame_code.co_freevars:
			load_opcodes = ('LOAD_DEREF',)
			name_table = frame_code.co_freevars
		else:
			# In the case that for some reason we can't find which var map we're stored in, then
			# just assume that we will not be yielded.
			return False

		# Chew through the rest of the bytecode to find our load points
		while index < len(code):
			opcode = opname[code[index]]
			if opcode in load_opcodes:
				# If we found a load op, the next byte should be the name index
				arg = code[index + 1]
				if name_table[arg] == name:
					# If the /very next/ op is a `YIELD` then we've been yielded
					if opname[code[index + 2]] == 'YIELD_VALUE':
						return True
					else:
						return False
				else:
					index += 2
			else:
				index += 2
		return False
	else:
		# If we don't have a name due to an assignment, then we look for a `GET_YIELD_FROM_ITER` right
		# after the call site.
		while True:
			opcode = opname[code[index]]
			if opcode == 'GET_YIELD_FROM_ITER':
				return True
			elif opcode in ('CACHE',):
				index += 2
			else:
				return False
