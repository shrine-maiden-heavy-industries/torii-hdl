# SPDX-License-Identifier: BSD-2-Clause
# torii: foo0=1, bar0=yes, baz0=enable, qux0=on, xyzzy0=enabled
# torii: foo1=0, bar1=no, baz1=disable, qux1=off, xyzzy1=disabled
# torii: foo2=0b1, bar2=0o2, baz2=0x3

from torii.test import ToriiTestCase
from torii.util import flatten, get_linter_option, get_linter_options, union

class MiscUtilsTestCase(ToriiTestCase):
	def test_flatten(self):
		self.assertEqual(list(flatten([])), [])
		self.assertEqual(list(flatten([[], [], []])), [])
		self.assertEqual(list(flatten([[[], [], []], []])), [])
		self.assertEqual(list(flatten([[[[], []], []], []])), [])
		self.assertEqual(list(flatten([[], [[], []], []])), [])
		self.assertEqual(list(flatten([[], [[0], []], []])), [0])
		self.assertEqual(list(flatten([[], [[], [], 0], []])), [0])
		self.assertEqual(list(flatten([[], [[], []], [0]])), [0])
		self.assertEqual(list(flatten([[], [[], []], [], 0])), [0])
		self.assertEqual(list(flatten([0, 1, 2, 3])), [0, 1, 2, 3])
		self.assertEqual(list(flatten([0, [1, 2], 3])), [0, 1, 2, 3])
		self.assertEqual(list(flatten([0, [1, [2, 3]]])), [0, 1, 2, 3])
		self.assertEqual(list(flatten([0, [1, 2], [3]])), [0, 1, 2, 3])
		self.assertEqual(list(flatten([0, [1, 2], [[3]]])), [0, 1, 2, 3])
		self.assertEqual(list(flatten([0, '1', object, 3.0])), [0, '1', object, 3.0])
		self.assertEqual(list(flatten([0, ['1', object], 3.0])), [0, '1', object, 3.0])
		self.assertEqual(list(flatten([0, ['1'], [object, 3.0]])), [0, '1', object, 3.0])
		self.assertEqual(list(flatten([[0, ['1'], [object, 3.0]]])), [0, '1', object, 3.0])

	def test_get_linter_option_invalid(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Expected type to be either \'bool\' or \'int\', not <class \'float\'>$',
		):
			get_linter_option(__file__, 'foo0', float, 0.0) # type: ignore

	def test_get_linter_option(self):
		self.assertEqual(get_linter_option(__file__, 'foo0', bool, False), True)
		self.assertEqual(get_linter_option(__file__, 'bar0', bool, False), True)
		self.assertEqual(get_linter_option(__file__, 'baz0', bool, False), True)
		self.assertEqual(get_linter_option(__file__, 'qux0', bool, False), True)
		self.assertEqual(get_linter_option(__file__, 'xyzzy0', bool, False), True)

		self.assertEqual(get_linter_option(__file__, 'foo1', bool, True), False)
		self.assertEqual(get_linter_option(__file__, 'bar1', bool, True), False)
		self.assertEqual(get_linter_option(__file__, 'baz1', bool, True), False)
		self.assertEqual(get_linter_option(__file__, 'qux1', bool, True), False)
		self.assertEqual(get_linter_option(__file__, 'xyzzy1', bool, True), False)

		self.assertEqual(get_linter_option(__file__, 'foo2', int, 0), 1)
		self.assertEqual(get_linter_option(__file__, 'bar2', int, 0), 2)
		self.assertEqual(get_linter_option(__file__, 'baz2', int, 0), 3)

		self.assertEqual(get_linter_option(__file__, 'foo3', int, 0), 0)
		self.assertEqual(get_linter_option(__file__, 'bar3', bool, True), False)
		self.assertEqual(get_linter_option(__file__, 'baz3', int, 0), 2)

		self.assertEqual(get_linter_option(__file__, 'NotFound32', int, 0), 0)

	def test_get_linter_options(self):
		self.assertEqual(get_linter_options(__file__), {
			'foo0': '1',
			'bar0': 'yes',
			'baz0': 'enable',
			'qux0': 'on',
			'xyzzy0': 'enabled',
			'foo1': '0',
			'bar1': 'no',
			'baz1': 'disable',
			'qux1': 'off',
			'xyzzy1': 'disabled',
			'foo2': '0b1',
			'bar2': '0o2',
			'baz2': '0x3',
			'foo3': 'invalid',
			'bar3': 'no',
			'baz3': '2'
		})

	def test_union(self):
		# TODO(aki): We should have a more "comprehensive" test, but it's pretty simple
		self.assertEqual(union([0, 1, 2, 3, 4]), 7)
		self.assertEqual(union([4, 6, 8], 2), 14)

# torii: foo3=invalid, bar3=no, baz3=2
