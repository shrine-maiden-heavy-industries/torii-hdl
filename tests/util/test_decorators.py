# SPDX-License-Identifier: BSD-2-Clause

import warnings

from torii.test import ToriiTestCase
from torii.util import decorators

class DecoratorsTestCase(ToriiTestCase):

	def test_memoize(self):
		hittest: int = 0

		with warnings.catch_warnings():
			# Ignore the new Deprecation warning
			warnings.simplefilter('ignore')

			@decorators.memoize
			def foo(a: int, b: int) -> int:
				nonlocal hittest
				hittest = hittest + 1
				return a * 2 + b

		self.assertEqual(hittest, 0)
		_ = foo(1, 2)
		self.assertEqual(hittest, 1)
		_ = foo(1, 2)
		self.assertEqual(hittest, 1)
		_ = foo(2, 1)
		self.assertEqual(hittest, 2)
		_ = foo(2, 1)
		self.assertEqual(hittest, 2)

	def test_final(self):

		@decorators.final
		class Foo:
			def __init__(self):
				pass # :nocov:

		with self.assertRaisesRegex(
			TypeError,
			r'^Subclassing tests.util.test_decorators.Foo is not supported$'
		):
			class Bar(Foo):
				def baz(self) -> None:
					pass # :nocov:

	def test_deprecated(self):

		@decorators.deprecated('meow')
		def foo() -> None:
			pass

		with self.assertWarnsRegex(DeprecationWarning, r'^meow$'):
			foo()

		pass

	def test_extend(self):

		class Foo:
			def __init__(self):
				pass

		self.assertFalse(hasattr(Foo, 'bar'))
		self.assertFalse(hasattr(Foo, 'baz'))

		with warnings.catch_warnings():
			# Ignore the new Deprecation warning
			warnings.simplefilter('ignore')

			@decorators.extend(Foo)
			def bar(self) -> int:
				return 1

		self.assertTrue(hasattr(Foo, 'bar'))
		self.assertFalse(hasattr(Foo, 'baz'))

		self.assertEqual(Foo().bar(), 1)

		with warnings.catch_warnings():
			# Ignore the new Deprecation warning
			warnings.simplefilter('ignore')

			@decorators.extend(Foo)
			@property
			def baz(self) -> int:
				return 2

		self.assertTrue(hasattr(Foo, 'bar'))
		self.assertTrue(hasattr(Foo, 'baz'))

		self.assertEqual(Foo().bar(), 1)
		self.assertEqual(Foo().baz, 2)
