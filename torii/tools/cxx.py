# SPDX-License-Identifier: BSD-2-Clause

from collections.abc                 import Generator, Iterable
from enum                            import Enum, auto, unique
from pathlib                         import Path
from shlex                           import split
from sysconfig                       import get_config_vars
from tempfile                        import TemporaryDirectory
from warnings                        import warn

# NOTE(aki): So this looks a little hokey, but should be "fine":tm:
from setuptools._distutils.ccompiler import CCompiler, new_compiler

from ..util.fs                       import working_dir

__all__ = (
	'compile_cxx',
	'build_cxx',
)

@unique
class ObjectType(Enum):
	''' Type of object we want to build '''
	EXEC  = auto()
	''' Output type is an executable binary '''
	LIB   = auto()
	''' Output type is a static library '''
	SHLIB = auto()
	''' Output type is a shared library '''

def _resolve_paths(paths: Iterable[str | Path]) -> Generator[str, None, None]:
	''' A simple helper to resolve and string-ify an Iterable of str and Path objects. '''

	return ( str(path.resolve()) if isinstance(path, Path) else path for path in paths )

# NOTE(aki):
# So, as an HDL we shouldn't really need to build C or C++ objects, but there are a few extenuating circumstances,
# primarily when building simulation sources for [cxxrtl] based simulations.
#
# While it would be nice if Meson was able to be consumed as a library so we can use it to do the platform agnostic
# compiler and linker driving, we're forced to use the setuptools/distutils way to drive them, which is, both painful
# and subtly broken in strange ways.
#
# So, until I decide to fork Meson, vivisect it to pull only the compiler and linker abstractions out, and turn it into
# a Python package, this will have to do for now.
#
# [cxxrtl]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_cxxrtl.html
def compile_cxx(
	name: str, /, output_dir: str | Path, source_files: Iterable[str | Path] | None,
	include_paths: Iterable[str | Path] | None = None, library_paths: Iterable[str | Path] | None = None,
	defines: dict[str, str] | None = None, output_type: ObjectType = ObjectType.SHLIB,
	*, source_listings: dict[str, str] | None = None, extra_libs: Iterable[str | Path] | None = None,
	extra_objs: Iterable[str | Path] | None = None, extra_cxx_opts: Iterable[str] | None = None,
	extra_ld_opts: Iterable[str] | None = None, verbose: bool = False, debug: bool = False
) -> Path:
	'''
	Build a binary object from the provided source files and compiler options.

	Parameters
	----------
	name : str
		The name of the output object without its suffix.

	output_dir : str | Path
		The output directory used for the intermediate and final build products.

	source_files : Iterable[str | Path] | None
		A list of C++ source files to build.

		This can be used to include extra or externally generated source files
		from tooling, this allows you to not need to read the file in to pass to the
		``source_listings`` argument which expects the full source of the file.

	include_paths : Iterable[str | Path] | None
		A list of extra include paths to pass to the compiler.

		default: None

	library_paths : Iterable[str | Path] | None
		A list of extra library search paths to pass to the compiler.

		default: None

	defines : dict[str, str] | None
		A collection of preprocessor definitions to pass to the compiler.

		default: None

	output_type : ObjectType
		The type of object to build.

		default: ObjectType.SHLIB

	source_listings : dict[str, str] | None
		A collection of ``filename: source listing`` pairs to include in the build.
		They will be written out to the build directory for inclusion in the build.

		If the file already exists on the filesystem, then it is recommended to pass the path
		of the file via the ``source_files`` parameter rather than reading the file into memory
		to pass here.

		default: None

	extra_libs : Iterable[str | Path] | None
		A list of extra libraries to link against.

		default: None

	extra_objs : Iterable[str | Path] | None
		A list of extra object files to link with.

		default: None

	extra_cxx_opts : Iterable[str] | None
		A list of extra options to pass to the compiler.

		default: None

	extra_ld_opts : Iterable[str] | None
		A list of extra options to pass to the linker.

		default: None

	verbose : bool
		Enable verbose compiler output.

		default: False

	debug : bool
		Build in debug mode.

		default: False

	Returns
	-------
	Path
		The path to the final output file from the compilation process.

	Raises
	------
	RuntimeError
		If we are not able to find any of the tools needed to build C++ binaries on this platform.

	distutils.errors.CompileError
		If the compilation of any of the source files fail.

	distutils.errors.LinkError
		If we are unable to link the final output binary.
	'''

	build_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir

	# NOTE(aki): We do this because `get_config_var`, calls this for each lookup anyway
	py_config = get_config_vars()

	# HACK(aki):
	# There should be a better way to do this, but it works:tm:
	# setuptools/distutils assumes a lot of things are relative paths, so we need to ensure we're in
	# the final build directory so we don't puke object files all over the place.
	with working_dir(build_dir) as cwd:
		# Compute where we dump out the source files
		src_dir = cwd / 'src'
		src_dir.mkdir(exist_ok = True)

		# Compute where the intermediate object files will be put
		obj_dir = cwd / 'build'
		obj_dir.mkdir(exist_ok = True)

		# Construct a new compiler
		cxx = new_compiler(verbose = verbose)

		# Try to get the compilers/linkers
		py_ar: str       = py_config.get('AR',          cxx.executables.get('archiver', ''))
		py_cc: str       = py_config.get('CC',          cxx.executables.get('compiler', ''))
		py_cxx: str      = py_config.get('CXX',         cxx.executables.get('compiler_cxx', ''))
		py_ldso_cc: str  = py_config.get('LDSHARED',    cxx.executables.get('linker_so', ''))
		py_ldso_cxx: str = py_config.get('LDCXXSHARED', cxx.executables.get('linker_so_cxx', ''))

		# Get the ancillary flags
		arflags: list[str] = py_config.get('ARFLAGS', '').split(' ')
		cflags: list[str]  = py_config.get('CCSHARED', '').split(' ')

		# Get the system include/lib dirs
		py_inc_dir: list[str] = py_config.get('INCLUDEDIR', '').split(':')
		py_lib_dir: list[str] = py_config.get('LIBDIR', '').split(':')

		# Ensure we have the needed tools
		if not all(
			binary.strip() != '' for binary in [
				py_ar, py_cc, py_cxx, py_ldso_cc, py_ldso_cxx
			]
		):
			# NOTE(aki): We don't have a good way to synthetically generate this case for testing, RIP
			raise RuntimeError('Can\'t determine platform compilers, unable to build C++ object') # :nocov:

		# Set the core executables
		cxx.set_executable('archiver', [*split(py_ar), *arflags])
		cxx.set_executable('compiler', [*split(py_cc), *cflags])
		cxx.set_executable('compiler_cxx', [*split(py_cxx), *cflags])
		cxx.set_executable('linker_so', [*split(py_ldso_cc), *cflags])
		cxx.set_executable('linker_so_cxx', [*split(py_ldso_cxx), *cflags])

		# Populate include directories
		for inc_dir in py_inc_dir:
			if inc_dir.strip() != '':
				cxx.add_include_dir(inc_dir)

		if include_paths is not None:
			for inc_dir in include_paths:
				cxx.add_include_dir(str(inc_dir))

		# Populate library search directories
		for lib_dir in py_lib_dir:
			if lib_dir.strip() != '':
				cxx.add_library_dir(lib_dir)

		if library_paths is not None:
			for lib_dir in library_paths:
				cxx.add_library_dir(str(lib_dir))

		# Populate defines
		if defines is not None:
			for (def_name, def_value) in defines.items():
				cxx.define_macro(def_name, def_value)

		src_files = list[str | Path]()

		# If we have any specified source paths populate those
		if source_files is not None:
			src_files += source_files

		# Dump out source listing
		if source_listings is not None:
			for (file_name, listing) in source_listings.items():
				src_name = src_dir / file_name
				src_files.append(src_name)

				with src_name.open('w') as src_file:
					src_file.write(listing)

		# Populate object files
		obj_files = list[str | Path]()

		if extra_objs is not None:
			obj_files += extra_objs

		obj_files += cxx.object_filenames(src_files, output_dir = obj_dir)

		# Compute the output object name
		match output_type:
			case ObjectType.EXEC:
				output_name = cwd / f'{name}{cxx.exe_extension if cxx.exe_extension is not None else ""}'
			case ObjectType.SHLIB:
				output_name = cwd / f'{name}{cxx.shared_lib_extension}'
			case ObjectType.LIB:
				output_name = cwd / f'{name}{cxx.static_lib_extension}'

		# XXX(aki):
		# This is kinda strange and messed up the output object name computation for the object file
		# takes the whole path and generates a weird nested structure, but it all links so until I have
		# the spoons to fix it, we'll just deal with it.

		# Generate the intermediate object files from the source files
		cxx.compile(
			src_files,
			output_dir = str(obj_dir),
			debug = debug,
			extra_preargs = [*cflags,] + list(extra_cxx_opts) if extra_cxx_opts is not None else []
		)

		# Link or archive the final object
		match output_type:
			case ObjectType.EXEC | ObjectType.SHLIB:
				cxx.link(
					CCompiler.EXECUTABLE if output_type == ObjectType.EXEC else CCompiler.SHARED_LIBRARY,
					list(_resolve_paths(obj_files)),
					output_filename = str(output_name),
					output_dir = str(cwd),
					libraries = list(_resolve_paths(extra_libs)) if extra_libs is not None else None,
					debug = debug,
					extra_preargs = list(extra_ld_opts) if extra_ld_opts is not None else None,
					target_lang = 'C++'
				)
			case ObjectType.LIB:
				cxx.create_static_lib(
					list(_resolve_paths(obj_files)),
					output_libname = str(output_name),
					output_dir = str(cwd),
					debug = debug,
					target_lang = 'C++'
				)

	return output_name

def build_cxx(
	cxx_sources: dict[str, str], output_name: str, include_dirs: list[str], macros: list[str]
)  -> tuple[TemporaryDirectory[str], str]:
	warn(
		'torii.tools.cxx.build_cxx has been deprecated in favor of torii.tools.cxx.compile_cxx',
		DeprecationWarning, stacklevel = 2
	)

	build_dir  = TemporaryDirectory(prefix = 'torii_cxx_')
	output_dir = Path(build_dir.name)

	output_file = compile_cxx(
		output_name, output_dir, None, include_paths = include_dirs, defines = {
			k: v for (k, v) in (macro.strip().split('=', 2) for macro in macros)
		},
		source_listings = cxx_sources
	)

	return (build_dir, output_file.name)
