# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl.time import (
	Frequency, aHz, fHz, pHz, nHz, uHz, mHz, cHz, dHz, Hz, DHz, hHz, kHz, MHz, GHz, THz, PHz, EHz
)
from torii.hdl.time import (
	Period, _as, fs, ps, ns, us, ms, cs, ds, s, das, hs, ks, Ms, Gs, Ts, Ps, Es
)

from unittest import TestCase

class FrequencyTestCase(TestCase):
	def test_units(self) -> None:
		self.assertAlmostEqual((1 * aHz)._value, 1e-18)
		self.assertAlmostEqual((1 * fHz)._value, 1e-15)
		self.assertAlmostEqual((1 * pHz)._value, 1e-12)
		self.assertAlmostEqual((1 * nHz)._value, 1e-9)
		self.assertAlmostEqual((1 * uHz)._value, 1e-6)
		self.assertAlmostEqual((1 * mHz)._value, 1e-3)
		self.assertAlmostEqual((1 * cHz)._value, 1e-2)
		self.assertAlmostEqual((1 * dHz)._value, 1e-1)
		self.assertAlmostEqual((1 * Hz)._value, 1)
		self.assertAlmostEqual((1 * DHz)._value, 1e1)
		self.assertAlmostEqual((1 * hHz)._value, 1e2)
		self.assertAlmostEqual((1 * kHz)._value, 1e3)
		self.assertAlmostEqual((1 * MHz)._value, 1e6)
		self.assertAlmostEqual((1 * GHz)._value, 1e9)
		self.assertAlmostEqual((1 * THz)._value, 1e12)
		self.assertAlmostEqual((1 * PHz)._value, 1e15)
		self.assertAlmostEqual((1 * EHz)._value, 1e18)

		self.assertAlmostEqual(aHz(5)._value, 5e-18)
		self.assertAlmostEqual(fHz(5)._value, 5e-15)
		self.assertAlmostEqual(pHz(5)._value, 5e-12)
		self.assertAlmostEqual(nHz(5)._value, 5e-9)
		self.assertAlmostEqual(uHz(5)._value, 5e-6)
		self.assertAlmostEqual(mHz(5)._value, 5e-3)
		self.assertAlmostEqual(cHz(5)._value, 5e-2)
		self.assertAlmostEqual(dHz(5)._value, 5e-1)
		self.assertAlmostEqual(Hz(5)._value, 5)
		self.assertAlmostEqual(DHz(5)._value, 5e1)
		self.assertAlmostEqual(hHz(5)._value, 5e2)
		self.assertAlmostEqual(kHz(5)._value, 5e3)
		self.assertAlmostEqual(MHz(5)._value, 5e6)
		self.assertAlmostEqual(GHz(5)._value, 5e9)
		self.assertAlmostEqual(THz(5)._value, 5e12)
		self.assertAlmostEqual(PHz(5)._value, 5e15)
		self.assertAlmostEqual(EHz(5)._value, 5e18)

		# BUG(aki): Due to floating points, the numerical certainty is unstable this low
		self.assertAlmostEqual(Frequency(2e-18)._value, aHz(2)._value)
		self.assertAlmostEqual(Frequency(3e-15)._value, fHz(3)._value)
		self.assertEqual(Frequency(4e-12), pHz(4))
		self.assertEqual(Frequency(5e-9), nHz(5))
		self.assertEqual(Frequency(6e-6), uHz(6))
		self.assertEqual(Frequency(7e-3), mHz(7))
		self.assertEqual(Frequency(8e-2), cHz(8))
		self.assertEqual(Frequency(9e-1), dHz(9))
		self.assertEqual(Frequency(10), Hz(10))
		self.assertEqual(Frequency(9e1), DHz(9))
		self.assertEqual(Frequency(8e2), hHz(8))
		self.assertEqual(Frequency(7e3), kHz(7))
		self.assertEqual(Frequency(6e6), MHz(6))
		self.assertEqual(Frequency(5e9), GHz(5))
		self.assertEqual(Frequency(4e12), THz(4))
		self.assertEqual(Frequency(3e15), PHz(3))
		self.assertEqual(Frequency(2e18), EHz(2))

	def test_format(self) -> None:
		self.assertEqual(f'{MHz(100)}', '100MHz')
		self.assertEqual(f'{MHz(100):GHz}', '0.1GHz')
		self.assertEqual(f'{MHz(100):kHz}', '100000kHz')
		self.assertEqual(f'{GHz(10):#MHz}', '10000')
		self.assertEqual(f'{kHz(123456789)}', '123.4568GHz')
		self.assertEqual(f'{kHz(123456789):.6}', '123.456789GHz')
		self.assertEqual(f'{kHz(123456789):THz.10}', '0.123456789THz')

	def test_conversion(self) -> None:
		self.assertEqual(MHz(100).period, ns(10))
		self.assertEqual(GHz(50).period, 20 * ps)

	def test_attributes(self) -> None:
		self.assertAlmostEqual(MHz(10).hertz, 10e6)
		self.assertAlmostEqual(kHz(100).megahertz, 0.1)
		self.assertAlmostEqual(Hz(1000).kilohertz, 1)
		self.assertAlmostEqual(MHz(25).gigahertz, 0.025)

class PeriodTestCase(TestCase):
	def test_units(self) -> None:
		self.assertAlmostEqual((1 * _as)._value, 1e-18)
		self.assertAlmostEqual((1 * fs)._value, 1e-15)
		self.assertAlmostEqual((1 * ps)._value, 1e-12)
		self.assertAlmostEqual((1 * ns)._value, 1e-9)
		self.assertAlmostEqual((1 * us)._value, 1e-6)
		self.assertAlmostEqual((1 * ms)._value, 1e-3)
		self.assertAlmostEqual((1 * cs)._value, 1e-2)
		self.assertAlmostEqual((1 * ds)._value, 1e-1)
		self.assertAlmostEqual((1 * s)._value, 1)
		self.assertAlmostEqual((1 * das)._value, 1e1)
		self.assertAlmostEqual((1 * hs)._value, 1e2)
		self.assertAlmostEqual((1 * ks)._value, 1e3)
		self.assertAlmostEqual((1 * Ms)._value, 1e6)
		self.assertAlmostEqual((1 * Gs)._value, 1e9)
		self.assertAlmostEqual((1 * Ts)._value, 1e12)
		self.assertAlmostEqual((1 * Ps)._value, 1e15)
		self.assertAlmostEqual((1 * Es)._value, 1e18)

		self.assertAlmostEqual(_as(5)._value, 5e-18)
		self.assertAlmostEqual(fs(5)._value, 5e-15)
		self.assertAlmostEqual(ps(5)._value, 5e-12)
		self.assertAlmostEqual(ns(5)._value, 5e-9)
		self.assertAlmostEqual(us(5)._value, 5e-6)
		self.assertAlmostEqual(ms(5)._value, 5e-3)
		self.assertAlmostEqual(cs(5)._value, 5e-2)
		self.assertAlmostEqual(ds(5)._value, 5e-1)
		self.assertAlmostEqual(s(5)._value, 5)
		self.assertAlmostEqual(das(5)._value, 5e1)
		self.assertAlmostEqual(hs(5)._value, 5e2)
		self.assertAlmostEqual(ks(5)._value, 5e3)
		self.assertAlmostEqual(Ms(5)._value, 5e6)
		self.assertAlmostEqual(Gs(5)._value, 5e9)
		self.assertAlmostEqual(Ts(5)._value, 5e12)
		self.assertAlmostEqual(Ps(5)._value, 5e15)
		self.assertAlmostEqual(Es(5)._value, 5e18)

		# BUG(aki): Due to floating points, the numerical certainty is unstable this low
		self.assertAlmostEqual(Period(2e-18)._value, _as(2)._value)
		self.assertAlmostEqual(Period(3e-15)._value, fs(3)._value)
		self.assertEqual(Period(4e-12), ps(4))
		self.assertEqual(Period(5e-9), ns(5))
		self.assertEqual(Period(6e-6), us(6))
		self.assertEqual(Period(7e-3), ms(7))
		self.assertEqual(Period(8e-2), cs(8))
		self.assertEqual(Period(9e-1), ds(9))
		self.assertEqual(Period(10), s(10))
		self.assertEqual(Period(9e1), das(9))
		self.assertEqual(Period(8e2), hs(8))
		self.assertEqual(Period(7e3), ks(7))
		self.assertEqual(Period(6e6), Ms(6))
		self.assertEqual(Period(5e9), Gs(5))
		self.assertEqual(Period(4e12), Ts(4))
		self.assertEqual(Period(3e15), Ps(3))
		self.assertEqual(Period(2e18), Es(2))

	def test_format(self) -> None:
		self.assertEqual(f'{ps(100)}', '100ps')
		self.assertEqual(f'{ps(100):ns}', '0.1ns')
		self.assertEqual(f'{ns(1):ps}', '1000.0ps') # TODO(aki): Figure out why this is happening
		self.assertEqual(f'{us(10):#ns}', '10000.0')
		self.assertEqual(f'{ps(123456789)}', '123.4568us')
		self.assertEqual(f'{ps(123456789):.6}', '123.456789us')
		self.assertEqual(f'{ps(123456789):ms.10}', '0.123456789ms')

	def test_conversion(self) -> None:
		self.assertEqual(ps(1).frequency, THz(1))
		self.assertEqual(50 * ns, MHz(20))

	def test_attributes(self) -> None:
		self.assertAlmostEqual(ms(100).seconds, 0.100)
		self.assertAlmostEqual(s(10).milliseconds, 10000)
		self.assertAlmostEqual(ns(25).microseconds, 0.025)
		self.assertAlmostEqual(us(2).picoseconds, 2000000)
