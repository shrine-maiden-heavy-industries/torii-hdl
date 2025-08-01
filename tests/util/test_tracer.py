# SPDX-License-Identifier: BSD-2-Clause

from types         import SimpleNamespace

from torii.hdl     import ast
from torii.hdl.ast import Signal
from torii.test    import ToriiTestCase

class TracerTestCase(ToriiTestCase):
	def test_fast(self):
		s1 = Signal()
		self.assertEqual(s1.name, 's1')
		s2 = Signal()
		self.assertEqual(s2.name, 's2')

	def test_call_variants(self):
		args = []
		kwargs = {}
		s1 = Signal()
		self.assertEqual(s1.name, 's1')
		s2 = Signal(reset=0)
		self.assertEqual(s2.name, 's2')
		s3 = Signal(*args, **kwargs)
		self.assertEqual(s3.name, 's3')
		s4 = ast.Signal()
		self.assertEqual(s4.name, 's4')
		s5 = ast.Signal(reset=0)
		self.assertEqual(s5.name, 's5')
		s6 = ast.Signal(*args, **kwargs)
		self.assertEqual(s6.name, 's6')

	def test_name(self):
		class Dummy:
			s1 = Signal()
			self.assertEqual(s1.name, 's1')
			s2 = Signal()
			self.assertEqual(s2.name, 's2')

	def test_attr(self):
		ns = SimpleNamespace()
		ns.s1 = Signal()
		self.assertEqual(ns.s1.name, 's1')
		ns.s2 = Signal()
		self.assertEqual(ns.s2.name, 's2')

	def test_index(self):
		lst = [None]
		lst[0] = Signal()
		self.assertEqual(lst[0].name, '$signal')

	def test_deref_cell(self):
		s1 = Signal()
		self.assertEqual(s1.name, 's1')
		s2 = Signal()
		self.assertEqual(s2.name, 's2')

		def dummy():
			return s1, s2 # :nocov:

	def test_deref_free(self):
		def inner():
			nonlocal s3, s4
			s3 = Signal()
			s4 = Signal()
			return s1, s2

		s1 = Signal()
		s2 = Signal()
		s3 = None
		s4 = None
		inner()
		self.assertEqual(s1.name, 's1')
		self.assertEqual(s2.name, 's2')
		self.assertEqual(s3.name, 's3')
		self.assertEqual(s4.name, 's4')

	def test_long(self):
		test = ''
		for i in range(100000):
			test += f'dummy{i} = None\n'
		test += 's1 = Signal()\n'
		test += 's2 = Signal()\n'
		ns = {'Signal': Signal}
		exec(test, ns)
		self.assertEqual(ns['s1'].name, 's1')
		self.assertEqual(ns['s2'].name, 's2')

	def test_deref_fast(self):
		def inner(s2):
			s1 = Signal()
			s2 = Signal()
			self.assertEqual(s1.name, 's1')
			self.assertEqual(s2.name, 's2')

			def dummy():
				return s1, s2 # :nocov:

		inner(None)
