# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl.ast import Shape, unsigned
from torii.hdl.rec import Direction
from torii.lib.io  import Pin, pin_layout

from ..utils       import ToriiTestSuiteCase

class PinLayoutTestCase(ToriiTestSuiteCase):
	def assertLayoutEqual(self, layout, expected):
		casted_layout = {}
		for name, (shape, dir) in layout.items():
			casted_layout[name] = (Shape.cast(shape), dir)

		self.assertEqual(casted_layout, expected)

class PinLayoutCombTestCase(PinLayoutTestCase):
	def test_pin_layout_i(self):
		layout_1 = pin_layout(1, dir = 'i')
		self.assertLayoutEqual(layout_1.fields, {
			'i': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'i')
		self.assertLayoutEqual(layout_2.fields, {
			'i': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_o(self):
		layout_1 = pin_layout(1, dir = 'o')
		self.assertLayoutEqual(layout_1.fields, {
			'o': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'o')
		self.assertLayoutEqual(layout_2.fields, {
			'o': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_oe(self):
		layout_1 = pin_layout(1, dir = 'oe')
		self.assertLayoutEqual(layout_1.fields, {
			'o':  (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'oe')
		self.assertLayoutEqual(layout_2.fields, {
			'o':  (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

	def test_pin_layout_io(self):
		layout_1 = pin_layout(1, dir = 'io')
		self.assertLayoutEqual(layout_1.fields, {
			'i':  (unsigned(1), Direction.NONE),
			'o':  (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'io')
		self.assertLayoutEqual(layout_2.fields, {
			'i':  (unsigned(2), Direction.NONE),
			'o':  (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

class PinLayoutSDRTestCase(PinLayoutTestCase):
	def test_pin_layout_i(self):
		layout_1 = pin_layout(1, dir = 'i', xdr = 1)
		self.assertLayoutEqual(layout_1.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'i', xdr = 1)
		self.assertLayoutEqual(layout_2.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_o(self):
		layout_1 = pin_layout(1, dir = 'o', xdr = 1)
		self.assertLayoutEqual(layout_1.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'o', xdr = 1)
		self.assertLayoutEqual(layout_2.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_oe(self):
		layout_1 = pin_layout(1, dir = 'oe', xdr = 1)
		self.assertLayoutEqual(layout_1.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o':  (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'oe', xdr = 1)
		self.assertLayoutEqual(layout_2.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o':  (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

	def test_pin_layout_io(self):
		layout_1 = pin_layout(1, dir = 'io', xdr = 1)
		self.assertLayoutEqual(layout_1.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i':  (unsigned(1), Direction.NONE),
			'o_clk': (unsigned(1), Direction.NONE),
			'o':  (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'io', xdr = 1)
		self.assertLayoutEqual(layout_2.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i':  (unsigned(2), Direction.NONE),
			'o_clk': (unsigned(1), Direction.NONE),
			'o':  (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

class PinLayoutDDRTestCase(PinLayoutTestCase):
	def test_pin_layout_i(self):
		layout_1 = pin_layout(1, dir = 'i', xdr = 2)
		self.assertLayoutEqual(layout_1.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i0': (unsigned(1), Direction.NONE),
			'i1': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'i', xdr = 2)
		self.assertLayoutEqual(layout_2.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i0': (unsigned(2), Direction.NONE),
			'i1': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_o(self):
		layout_1 = pin_layout(1, dir = 'o', xdr = 2)
		self.assertLayoutEqual(layout_1.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(1), Direction.NONE),
			'o1': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'o', xdr = 2)
		self.assertLayoutEqual(layout_2.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(2), Direction.NONE),
			'o1': (unsigned(2), Direction.NONE),
		})

	def test_pin_layout_oe(self):
		layout_1 = pin_layout(1, dir = 'oe', xdr = 2)
		self.assertLayoutEqual(layout_1.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(1), Direction.NONE),
			'o1': (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'oe', xdr = 2)
		self.assertLayoutEqual(layout_2.fields, {
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(2), Direction.NONE),
			'o1': (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

	def test_pin_layout_io(self):
		layout_1 = pin_layout(1, dir = 'io', xdr = 2)
		self.assertLayoutEqual(layout_1.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i0': (unsigned(1), Direction.NONE),
			'i1': (unsigned(1), Direction.NONE),
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(1), Direction.NONE),
			'o1': (unsigned(1), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

		layout_2 = pin_layout(2, dir = 'io', xdr = 2)
		self.assertLayoutEqual(layout_2.fields, {
			'i_clk': (unsigned(1), Direction.NONE),
			'i0': (unsigned(2), Direction.NONE),
			'i1': (unsigned(2), Direction.NONE),
			'o_clk': (unsigned(1), Direction.NONE),
			'o0': (unsigned(2), Direction.NONE),
			'o1': (unsigned(2), Direction.NONE),
			'oe': (unsigned(1), Direction.NONE),
		})

class PinTestCase(ToriiTestSuiteCase):
	def test_attributes(self):
		pin = Pin(2, dir = 'io', xdr = 2)
		self.assertEqual(pin.width, 2)
		self.assertEqual(pin.dir,   'io')
		self.assertEqual(pin.xdr,   2)
