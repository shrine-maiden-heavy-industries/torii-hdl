# SPDX-License-Identifier: BSD-2-Clause

from torii.lib.stream.simple import StreamInterface

from ....utils               import ToriiTestSuiteCase

class StreamInterfaceTestCase(ToriiTestSuiteCase):

	def test_record(self) -> None:
		s0 = StreamInterface()
		self.assertRepr(s0, '(rec s0 data valid first last ready)')

		s1 = StreamInterface(extra = [('meow', 8)])
		self.assertRepr(s1, '(rec s1 data valid first last ready meow)')

		s2 = StreamInterface(name = 'ULPI')
		self.assertRepr(s2, '(rec ULPI data valid first last ready)')

	def test_sizes(self) -> None:
		s0 = StreamInterface()
		self.assertEqual(s0.data.width,  8)
		self.assertEqual(s0.valid.width, 1)

		s1 = StreamInterface(data_width = 32, valid_width = None)
		self.assertEqual(s1.data.width,  32)
		self.assertEqual(s1.valid.width,  4)

		s2 = StreamInterface(data_width = 16, valid_width = 8)
		self.assertEqual(s2.data.width,  16)
		self.assertEqual(s2.valid.width,  8)
