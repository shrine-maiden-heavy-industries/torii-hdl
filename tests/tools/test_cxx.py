# SPDX-License-Identifier: BSD-2-Clause

import warnings
from ctypes          import cdll
from pathlib         import Path
from subprocess      import check_call
from tempfile        import TemporaryDirectory

from torii.test      import ToriiTestCase
from torii.tools.cxx import ObjectType, build_cxx, compile_cxx

class ToolchainCxxOldTestCase(ToriiTestCase):
	def setUp(self):
		self.include_dir = None
		self.build_dir = None

	def tearDown(self):
		if self.include_dir:
			self.include_dir.cleanup()

		if self.build_dir:
			self.build_dir.cleanup()

	def test_filename(self):
		with warnings.catch_warnings():
			warnings.simplefilter('ignore')

			self.build_dir, filename = build_cxx(
				cxx_sources = {'test.cc': ''},
				output_name = 'answer',
				include_dirs = [],
				macros = [],
			)

			self.assertTrue(filename.startswith('answer'))

	def test_simple(self):
		with warnings.catch_warnings():
			warnings.simplefilter('ignore')

			self.build_dir, filename = build_cxx(
				cxx_sources = {
					'test.cc': '''
						extern "C" int answer() { return 42; }
					'''
				},
				output_name = 'answer',
				include_dirs = [],
				macros = [],
			)

			library = cdll.LoadLibrary(str(Path(self.build_dir.name) / filename))
			self.assertEqual(library.answer(), 42)

	def test_macro(self):
		with warnings.catch_warnings():
			warnings.simplefilter('ignore')

			self.build_dir, filename = build_cxx(
				cxx_sources = {
					'test.cc': '''
						extern "C" int answer() { return ANSWER; }
					'''
				},
				output_name = 'answer',
				include_dirs = [],
				macros = ['ANSWER = 42'],
			)

			library = cdll.LoadLibrary(str(Path(self.build_dir.name) / filename))
			self.assertEqual(library.answer(), 42)

	def test_include(self):
		self.include_dir = TemporaryDirectory(prefix = 'torii_hxx_')

		with (Path(self.include_dir.name) / 'answer.h').open('w') as f:
			f.write('#define ANSWER 42')

		with warnings.catch_warnings():
			warnings.simplefilter('ignore')

			self.build_dir, filename = build_cxx(
				cxx_sources = {
					'test.cc': '''
						#include "answer.h"
						extern "C" int answer() { return ANSWER; }
					'''
				},
				output_name = 'answer',
				include_dirs = [self.include_dir.name],
				macros = [],
			)

			library = cdll.LoadLibrary(str(Path(self.build_dir.name) / filename))
			self.assertEqual(library.answer(), 42)

class ToolchainCxxTestCase(ToriiTestCase):

	def test_empty(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx('dummy', out_dir, None)

		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		temp.cleanup()

	def test_src_listings(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': '',
				'test1.cc': '',
				'test2.cc': '',
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test1.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test2.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		temp.cleanup()

	def test_src_interlink(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': 'int a();\nint b();\nint foo() { return a() + b(); }\n',
				'test1.cc': 'int a() { return 1; }\n',
				'test2.cc': 'int b() { return 2; }\n',
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test1.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test2.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		temp.cleanup()

	def test_ext_srcs(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		temp_src_dir = TemporaryDirectory()
		tmp_src = (Path(temp_src_dir.name) / 'test0.cc')
		with tmp_src.open('w') as f:
			f.write('')

		res_file = compile_cxx('dummy', out_dir, [ tmp_src ])

		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		temp.cleanup()
		temp_src_dir.cleanup()

# TODO(aki): These are a little more of a pain in the butt to test, they *should* work but
# 	def test_ext_objs(self):
# 		temp = TemporaryDirectory()
# 		out_dir = Path(temp.name)
#
# 		temp.cleanup()
#
# 	def test_lib_paths(self):
# 		temp = TemporaryDirectory()
# 		out_dir = Path(temp.name)
#
# 		temp.cleanup()
#
# 	def test_ext_libs(self):
# 		temp = TemporaryDirectory()
# 		out_dir = Path(temp.name)
#
# 		temp.cleanup()

	def test_extra_cxx_opts(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': 'extern "C" int value() { return 0xCA75; }\n',
			},
			extra_cxx_opts = [
				'-Wall', '-Wextra', '-Wpedantic'
			]
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		lib = cdll.LoadLibrary(str(res_file))
		self.assertEqual(lib.value(), 0xCA75)

		temp.cleanup()

	def test_extra_ld_opts(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': 'extern "C" int value() { return 0xCA75; }\n',
			},
			extra_ld_opts = [
				'-Wl,--gc-sections'
			]
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		lib = cdll.LoadLibrary(str(res_file))
		self.assertEqual(lib.value(), 0xCA75)

		temp.cleanup()

	def test_defines(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': 'extern "C" int value() { return VALUE; }\n',
			},
			defines = {
				'VALUE': '0xCA75'
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		lib = cdll.LoadLibrary(str(res_file))
		self.assertEqual(lib.value(), 0xCA75)

		temp.cleanup()

	def test_inc_paths(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		inc_dir = TemporaryDirectory()

		with (Path(inc_dir.name) / 'value.hh').open('w') as f:
			f.write('#define VALUE 0xCA75')

		res_file = compile_cxx(
			'dummy', out_dir, None,
			source_listings = {
				'test0.cc': '#include "value.hh"\nextern "C" int value() { return VALUE; }\n',
			},
			include_paths = [
				inc_dir.name
			]
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		lib = cdll.LoadLibrary(str(res_file))
		self.assertEqual(lib.value(), 0xCA75)

		temp.cleanup()
		inc_dir.cleanup()

	def test_shlib(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None, output_type = ObjectType.SHLIB,
			source_listings = {
				'test0.cc': 'extern "C" int value() { return 0xCA75; }\n',
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		lib = cdll.LoadLibrary(str(res_file))
		self.assertEqual(lib.value(), 0xCA75)

		temp.cleanup()

	def test_exec(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None, output_type = ObjectType.EXEC,
			source_listings = {
				'test0.cc': 'int main(int,char**) { return 0; }\n',
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		self.assertEqual(check_call(res_file), 0)

		temp.cleanup()

	def test_lib(self):
		temp = TemporaryDirectory()
		out_dir = Path(temp.name)

		res_file = compile_cxx(
			'dummy', out_dir, None, output_type = ObjectType.LIB,
			source_listings = {
				'test0.cc': 'int a() { return 0; }\n',
				'test1.cc': 'int b() { return 1; }\n',
				'test2.cc': 'int c() { return 2; }\n',
			}
		)

		self.assertTrue((out_dir / 'src' / 'test0.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test1.cc').exists())
		self.assertTrue((out_dir / 'src' / 'test2.cc').exists())
		self.assertEqual(res_file.stem, 'dummy')
		self.assertEqual(res_file.parent, out_dir)

		temp.cleanup()
