# SPDX-License-Identifier: BSD-2-Clause

from torii.build.dsl               import Attrs
from torii.platform.resources.user import (
	_SplitResources, LEDResources, ButtonResources, SwitchResources
)
from torii.test                    import ToriiTestCase


class ResourcesTestCase(ToriiTestCase):

	def test_split_resources(self):
		resources = _SplitResources(pins = 'A B C D E', default_name = 'test', dir = 'io')

		self.assertEqual(len(resources), 5)

		for idx, res in enumerate(resources):
			self.assertEqual(len(res.ios), 1)
			self.assertEqual(res.name, 'test')
			self.assertEqual(res.number, idx)

	def test_led_resources(self):
		leds = LEDResources(pins = 'A B C D E F', attrs = Attrs(IO_TYPE = 'LVCMOS33'))

		self.assertEqual(len(leds), 6)

		for idx, res in enumerate(leds):
			self.assertTrue('IO_TYPE' in res.attrs.keys())
			self.assertEqual(len(res.ios), 1)
			self.assertEqual(res.ios[0].dir, 'o')
			self.assertEqual(res.name, 'led')
			self.assertEqual(res.number, idx)


	def test_button_resources(self):
		btns = ButtonResources(pins = 'A B C D E F G H', attrs = Attrs(IO_TYPE = 'LVCMOS33'))

		self.assertEqual(len(btns), 8)

		for idx, res in enumerate(btns):
			self.assertTrue('IO_TYPE' in res.attrs.keys())
			self.assertEqual(len(res.ios), 1)
			self.assertEqual(res.ios[0].dir, 'i')
			self.assertEqual(res.name, 'button')
			self.assertEqual(res.number, idx)

	def test_switch_resources(self):
		swtchs = SwitchResources(pins = 'A B C D E F G H I J K', attrs = Attrs(IO_TYPE = 'LVCMOS33'))

		self.assertEqual(len(swtchs), 11)

		for idx, res in enumerate(swtchs):
			self.assertTrue('IO_TYPE' in res.attrs.keys())
			self.assertEqual(len(res.ios), 1)
			self.assertEqual(res.ios[0].dir, 'i')
			self.assertEqual(res.name, 'switch')
			self.assertEqual(res.number, idx)
