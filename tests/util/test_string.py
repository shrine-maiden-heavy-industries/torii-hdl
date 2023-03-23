# SPDX-License-Identifier: BSD-2-Clause

from torii.util import string as util_string
from torii.test import ToriiTestCase

class StringUtilTestCase(ToriiTestCase):

	def test_ascii_escape(self):
		self.assertEqual(util_string.ascii_escape('abcdefg12346_'), 'abcdefg12346_')
		self.assertEqual(
			util_string.ascii_escape('-!@#$%^&*()'),
			''.join(map(lambda c: f'_{ord(c):02x}_', '-!@#$%^&*()'))
		)
		self.assertEqual(util_string.ascii_escape('nya~'), 'nya_7e_')

	def test_tcl_escape(self):
		self.assertEqual(util_string.tcl_escape('uwu'), '{uwu}')
		self.assertEqual(util_string.tcl_escape('"n"{y}a'), '{"n"\\{y\\}a}')
		self.assertEqual(
			util_string.tcl_escape(r'(fo"o\)B"ar[B{a}Z]'),
			'{(fo"o\\\\)B"ar[B\\{a\\}Z]}'
		)

	def test_tcl_quote(self):
		self.assertEqual(util_string.tcl_quote('test'), '"test"')
		self.assertEqual(util_string.tcl_quote('test"123'), '"test\\"123"')
		self.assertEqual(util_string.tcl_quote('test[123'), '"test\\[123"')
		self.assertEqual(util_string.tcl_quote('test$123'), '"test\\$123"')
		self.assertEqual(util_string.tcl_quote('"test$123['), '"\\"test\\$123\\["')
