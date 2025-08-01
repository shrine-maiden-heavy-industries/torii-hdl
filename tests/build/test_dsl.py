# SPDX-License-Identifier: BSD-2-Clause

from collections     import OrderedDict

from torii.build.dsl import (
	Attrs, Clock, Connector, DiffPairs, DiffPairsN, Pins, PinsN, Resource, Subsignal,
)

from ..utils         import ToriiTestSuiteCase

class PinsTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		p = Pins('A0 A1 A2')
		self.assertEqual(repr(p), '(pins io A0 A1 A2)')
		self.assertEqual(len(p.names), 3)
		self.assertEqual(p.dir, 'io')
		self.assertEqual(p.invert, False)
		self.assertEqual(list(p), ['A0', 'A1', 'A2'])

	def test_invert(self):
		p = PinsN('A0')
		self.assertEqual(repr(p), '(pins-n io A0)')
		self.assertEqual(p.invert, True)

	def test_invert_arg(self):
		p = Pins('A0', invert = True)
		self.assertEqual(p.invert, True)

	def test_conn(self):
		p = Pins('0 1 2', conn = ('pmod', 0))
		self.assertEqual(list(p), ['pmod_0:0', 'pmod_0:1', 'pmod_0:2'])
		p = Pins('0 1 2', conn = ('pmod', 'a'))
		self.assertEqual(list(p), ['pmod_a:0', 'pmod_a:1', 'pmod_a:2'])

	def test_map_names(self):
		p = Pins('0 1 2', conn = ('pmod', 0))
		mapping = {
			'pmod_0:0': 'A0',
			'pmod_0:1': 'A1',
			'pmod_0:2': 'A2',
		}
		self.assertEqual(p.map_names(mapping, p), ['A0', 'A1', 'A2'])

	def test_map_names_recur(self):
		p = Pins('0', conn = ('pmod', 0))
		mapping = {
			'pmod_0:0': 'ext_0:1',
			'ext_0:1':  'A1',
		}
		self.assertEqual(p.map_names(mapping, p), ['A1'])

	def test_wrong_names(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Names must be a whitespace-separated string, not \[\'A0\', \'A1\', \'A2\'\]$'
		):
			Pins(['A0', 'A1', 'A2'])

	def test_wrong_dir(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Direction must be one of \'i\', \'o\', \'oe\', or \'io\', not \'wrong\'$'
		):
			Pins('A0 A1', dir = 'wrong')

	def test_wrong_conn(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Connector must be None or a pair of string \(connector name\) and '
				r'integer\/string \(connector number\), not \(\'foo\', None\)$'
			)
		):
			Pins('A0 A1', conn = ('foo', None))

	def test_wrong_map_names(self):
		p = Pins('0 1 2', conn = ('pmod', 0))
		mapping = {
			'pmod_0:0': 'A0',
		}
		with self.assertRaisesRegex(
			NameError, (
				r'^Resource \(pins io pmod_0:0 pmod_0:1 pmod_0:2\) refers to nonexistent '
				r'connector pin pmod_0:1$'
			)
		):
			p.map_names(mapping, p)

	def test_wrong_assert_width(self):
		with self.assertRaisesRegex(
			AssertionError,
			r'^3 names are specified \(0 1 2\), but 4 names are expected$'
		):
			Pins('0 1 2', assert_width = 4)

class DiffPairsTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		dp = DiffPairs(p = 'A0 A1', n = 'B0 B1')
		self.assertEqual(repr(dp), '(diffpairs io (p A0 A1) (n B0 B1))')
		self.assertEqual(dp.p.names, ['A0', 'A1'])
		self.assertEqual(dp.n.names, ['B0', 'B1'])
		self.assertEqual(dp.dir, 'io')
		self.assertEqual(list(dp), [('A0', 'B0'), ('A1', 'B1')])

	def test_invert(self):
		dp = DiffPairsN(p = 'A0', n = 'B0')
		self.assertEqual(repr(dp), '(diffpairs-n io (p A0) (n B0))')
		self.assertEqual(dp.p.names, ['A0'])
		self.assertEqual(dp.n.names, ['B0'])
		self.assertEqual(dp.invert, True)

	def test_invert_arg(self):
		dp = DiffPairs(p = 'A0', n = 'B0', invert = True)
		self.assertEqual(dp.invert, True)

	def test_conn(self):
		dp = DiffPairs(p = '0 1 2', n = '3 4 5', conn = ('pmod', 0))
		self.assertEqual(list(dp), [
			('pmod_0:0', 'pmod_0:3'),
			('pmod_0:1', 'pmod_0:4'),
			('pmod_0:2', 'pmod_0:5'),
		])

	def test_dir(self):
		dp = DiffPairs('A0', 'B0', dir = 'o')
		self.assertEqual(dp.dir, 'o')
		self.assertEqual(dp.p.dir, 'o')
		self.assertEqual(dp.n.dir, 'o')

	def test_wrong_width(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Positive and negative pins must have the same width, but \(pins io A0\) '
				r'and \(pins io B0 B1\) do not$'
			)
		):
			DiffPairs('A0', 'B0 B1')

	def test_wrong_assert_width(self):
		with self.assertRaisesRegex(
			AssertionError,
			r'^3 names are specified \(0 1 2\), but 4 names are expected$'
		):
			DiffPairs('0 1 2', '3 4 5', assert_width = 4)

class AttrsTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		a = Attrs(IO_STANDARD = 'LVCMOS33', PULLUP = 1)
		self.assertEqual(a['IO_STANDARD'], 'LVCMOS33')
		self.assertEqual(repr(a), '(attrs IO_STANDARD=\'LVCMOS33\' PULLUP=1)')

	def test_remove(self):
		a = Attrs(FOO = None)
		self.assertEqual(a['FOO'], None)
		self.assertEqual(repr(a), '(attrs !FOO)')

	def test_callable(self):
		def fn(self):
			return 'FOO' # :nocov:

		a = Attrs(FOO = fn)
		self.assertEqual(a['FOO'], fn)
		self.assertEqual(repr(a), f'(attrs FOO={fn!r})')

	def test_wrong_value(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Value of attribute FOO must be None, int, str, or callable, not 1\.0$'
		):
			Attrs(FOO = 1.0)

class ClockTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		c = Clock(1_000_000)
		self.assertEqual(c.frequency, 1e6)
		self.assertEqual(c.period, 1e-6)
		self.assertEqual(repr(c), '(clock 1000000.0)')

	def test_from_khz(self):
		c = Clock.from_khz(20)
		self.assertEqual(c.frequency, 20e3)
		self.assertEqual(c.period, 50e-6)
		self.assertEqual(repr(c), '(clock 20000.0)')

	def test_from_mhz(self):
		c = Clock.from_mhz(300)
		self.assertEqual(c.frequency, 300e6)
		self.assertAlmostEqual(c.period, 300e-11)
		self.assertEqual(repr(c), '(clock 300000000.0)')

	def test_from_ghz(self):
		c = Clock.from_ghz(8)
		self.assertEqual(c.frequency, 8e9)
		self.assertAlmostEqual(c.period, 8e-15)
		self.assertEqual(repr(c), '(clock 8000000000.0)')

class SubsignalTestCase(ToriiTestSuiteCase):
	def test_basic_pins(self):
		s = Subsignal('a', Pins('A0'), Attrs(IOSTANDARD = 'LVCMOS33'))
		self.assertEqual(
			repr(s),
			'(subsignal a (pins io A0) (attrs IOSTANDARD=\'LVCMOS33\'))'
		)

	def test_basic_diffpairs(self):
		s = Subsignal('a', DiffPairs('A0', 'B0'))
		self.assertEqual(
			repr(s),
			'(subsignal a (diffpairs io (p A0) (n B0)))'
		)

	def test_basic_subsignals(self):
		s = Subsignal('a',
			Subsignal('b', Pins('A0')),
			Subsignal('c', Pins('A1'))
		)
		self.assertEqual(
			repr(s),
			'(subsignal a (subsignal b (pins io A0)) '
			'(subsignal c (pins io A1)))'
		)

	def test_attrs(self):
		s = Subsignal('a',
			Subsignal('b', Pins('A0')),
			Subsignal('c', Pins('A0'), Attrs(SLEW = 'FAST')),
			Attrs(IOSTANDARD = 'LVCMOS33')
		)
		self.assertEqual(s.attrs, {'IOSTANDARD': 'LVCMOS33'})
		self.assertEqual(s.ios[0].attrs, {})
		self.assertEqual(s.ios[1].attrs, {'SLEW': 'FAST'})

	def test_attrs_many(self):
		s = Subsignal('a', Pins('A0'), Attrs(SLEW = 'FAST'), Attrs(PULLUP = '1'))
		self.assertEqual(s.attrs, {'SLEW': 'FAST', 'PULLUP': '1'})

	def test_clock(self):
		s = Subsignal('a', Pins('A0'), Clock(1e6))
		self.assertEqual(s.clock.frequency, 1e6)

	def test_wrong_empty_io(self):
		with self.assertRaisesRegex(ValueError, r'^Missing I\/O constraints$'):
			Subsignal('a')

	def test_wrong_io(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Constraint must be one of Pins, DiffPairs, Subsignal, Attrs, or Clock, '
				r'not \'wrong\'$'
			)
		):
			Subsignal('a', 'wrong')

	def test_wrong_pins(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Pins and DiffPairs are incompatible with other location or subsignal '
				r'constraints, but \(pins io A1\) appears after \(pins io A0\)$'
			)
		):
			Subsignal('a', Pins('A0'), Pins('A1'))

	def test_wrong_diffpairs(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Pins and DiffPairs are incompatible with other location or subsignal '
				r'constraints, but \(pins io A1\) appears after \(diffpairs io \(p A0\) \(n B0\)\)$'
			)
		):
			Subsignal('a', DiffPairs('A0', 'B0'), Pins('A1'))

	def test_wrong_subsignals(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Pins and DiffPairs are incompatible with other location or subsignal '
				r'constraints, but \(pins io B0\) appears after \(subsignal b \(pins io A0\)\)$'
			)
		):
			Subsignal('a', Subsignal('b', Pins('A0')), Pins('B0'))

	def test_wrong_clock(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Clock constraint can only be applied to Pins or DiffPairs, not '
				r'\(subsignal b \(pins io A0\)\)$'
			)
		):
			Subsignal('a', Subsignal('b', Pins('A0')), Clock(1e6))

	def test_wrong_clock_many(self):
		with self.assertRaisesRegex(
			ValueError,
			r'^Clock constraint can be applied only once$'
		):
			Subsignal('a', Pins('A0'), Clock(1e6), Clock(1e7))

class ResourceTestCase(ToriiTestSuiteCase):
	def test_basic(self):
		r = Resource('serial', 0,
			Subsignal('tx', Pins('A0', dir = 'o')),
			Subsignal('rx', Pins('A1', dir = 'i')),
			Attrs(IOSTANDARD = 'LVCMOS33')
		)
		self.assertEqual(
			repr(r),
			'(resource serial 0'
			' (subsignal tx (pins o A0))'
			' (subsignal rx (pins i A1))'
			' (attrs IOSTANDARD=\'LVCMOS33\'))'
		)

	def test_number_wrong(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Resource number must be an integer, not \(pins o 1\)$'
		):
			# number omitted by accident
			Resource('led', Pins('1', dir = 'o'))

	def test_family(self):
		ios = [Subsignal('clk', Pins('A0', dir = 'o'))]
		r1  = Resource.family(0, default_name = 'spi', ios = ios)
		r2  = Resource.family('spi_flash', 0, default_name = 'spi', ios = ios)
		r3  = Resource.family('spi_flash', 0, default_name = 'spi', ios = ios, name_suffix = '4x')
		r4  = Resource.family(0, default_name = 'spi', ios = ios, name_suffix = '2x')
		self.assertEqual(r1.name, 'spi')
		self.assertEqual(r1.ios, ios)
		self.assertEqual(r2.name, 'spi_flash')
		self.assertEqual(r2.ios, ios)
		self.assertEqual(r3.name, 'spi_flash_4x')
		self.assertEqual(r3.ios, ios)
		self.assertEqual(r4.name, 'spi_2x')
		self.assertEqual(r4.ios, ios)

class ConnectorTestCase(ToriiTestSuiteCase):
	def test_string(self):
		c = Connector('pmod', 0, 'A0 A1 A2 A3 - - A4 A5 A6 A7 - -')
		self.assertEqual(c.name, 'pmod')
		self.assertEqual(c.number, 0)
		self.assertEqual(c.mapping, OrderedDict([
			('1', 'A0'),
			('2', 'A1'),
			('3', 'A2'),
			('4', 'A3'),
			('7', 'A4'),
			('8', 'A5'),
			('9', 'A6'),
			('10', 'A7'),
		]))
		self.assertEqual(list(c), [
			('pmod_0:1', 'A0'),
			('pmod_0:2', 'A1'),
			('pmod_0:3', 'A2'),
			('pmod_0:4', 'A3'),
			('pmod_0:7', 'A4'),
			('pmod_0:8', 'A5'),
			('pmod_0:9', 'A6'),
			('pmod_0:10', 'A7'),
		])
		self.assertEqual(
			repr(c),
			'(connector pmod 0 1=>A0 2=>A1 3=>A2 4=>A3 7=>A4 8=>A5 9=>A6 10=>A7)'
		)

	def test_dict(self):
		c = Connector('ext', 1, {'DP0': 'A0', 'DP1': 'A1'})
		self.assertEqual(c.name, 'ext')
		self.assertEqual(c.number, 1)
		self.assertEqual(c.mapping, OrderedDict([
			('DP0', 'A0'),
			('DP1', 'A1'),
		]))

	def test_conn(self):
		c = Connector('pmod', 0, '0 1 2 3 - - 4 5 6 7 - -', conn = ('expansion', 0))
		self.assertEqual(c.mapping, OrderedDict([
			('1', 'expansion_0:0'),
			('2', 'expansion_0:1'),
			('3', 'expansion_0:2'),
			('4', 'expansion_0:3'),
			('7', 'expansion_0:4'),
			('8', 'expansion_0:5'),
			('9', 'expansion_0:6'),
			('10', 'expansion_0:7'),
		]))

	def test_str_name(self):
		c = Connector('ext', 'A', '0 1 2')
		self.assertEqual(c.name, 'ext')
		self.assertEqual(c.number, 'A')

	def test_conn_wrong_name(self):
		with self.assertRaisesRegex(
			TypeError, (
				r'^Connector must be None or a pair of string \(connector name\) and '
				r'integer\/string \(connector number\), not \(\'foo\', None\)$'
			)
		):
			Connector('ext', 'A', '0 1 2', conn = ('foo', None))

	def test_wrong_io(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Connector I\/Os must be a dictionary or a string, not \[\]$'
		):
			Connector('pmod', 0, [])

	def test_wrong_dict_key_value(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^Connector pin name must be a string, not 0$'
		):
			Connector('pmod', 0, {0: 'A'})
		with self.assertRaisesRegex(
			TypeError,
			r'^Platform pin name must be a string, not 0$'
		):
			Connector('pmod', 0, {'A': 0})
