# SPDX-License-Identifier: BSD-2-Clause

from torii.test import ToriiTestCase
from torii.util import decorators

class DecoratorsTestCase(ToriiTestCase):

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
