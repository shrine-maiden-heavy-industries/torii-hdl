# SPDX-License-Identifier: BSD-2-Clause

from torii.diagnostics import ToriiSyntaxError
from torii.hdl.time    import (
	Frequency, aHz, fHz, pHz, nHz, uHz, mHz, cHz, dHz, Hz, DHz, hHz, kHz, MHz, GHz, THz, PHz, EHz
)
from torii.hdl.time    import (
	Period, _as, fs, ps, ns, us, ms, cs, ds, s, das, hs, ks, Ms, Gs, Ts, Ps, Es
)

from unittest          import TestCase

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

	def test_repr(self) -> None:
		self.assertEqual(f'{aHz(50)!r}', '(frequency 50aHz)')
		self.assertEqual(f'{fHz(50)!r}', '(frequency 50fHz)')
		self.assertEqual(f'{pHz(50)!r}', '(frequency 50pHz)')
		self.assertEqual(f'{nHz(50)!r}', '(frequency 50nHz)')
		self.assertEqual(f'{uHz(50)!r}', '(frequency 50uHz)')
		self.assertEqual(f'{mHz(50)!r}', '(frequency 50mHz)')
		self.assertEqual(f'{cHz(50)!r}', '(frequency 500mHz)')
		self.assertEqual(f'{dHz(5)!r}', '(frequency 500mHz)')
		self.assertEqual(f'{Hz(50)!r}', '(frequency 50Hz)')
		self.assertEqual(f'{DHz(50)!r}', '(frequency 500Hz)')
		self.assertEqual(f'{hHz(50)!r}', '(frequency 5kHz)')
		self.assertEqual(f'{kHz(50)!r}', '(frequency 50kHz)')
		self.assertEqual(f'{MHz(50)!r}', '(frequency 50MHz)')
		self.assertEqual(f'{GHz(50)!r}', '(frequency 50GHz)')
		self.assertEqual(f'{THz(50)!r}', '(frequency 50THz)')
		self.assertEqual(f'{PHz(50)!r}', '(frequency 50PHz)')
		self.assertEqual(f'{EHz(50)!r}', '(frequency 50EHz)')

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

	def test_comparison_lt(self) -> None:
		# Frequency-to-Frequency
		self.assertLess(aHz(1), fHz(1))
		self.assertLess(fHz(1), pHz(1))
		self.assertLess(pHz(1), nHz(1))
		self.assertLess(nHz(1), uHz(1))
		self.assertLess(uHz(1), mHz(1))
		self.assertLess(mHz(1), cHz(1))
		self.assertLess(cHz(1), dHz(1))
		self.assertLess(dHz(1), Hz(1))
		self.assertLess(Hz(1),  DHz(1))
		self.assertLess(DHz(1), hHz(1))
		self.assertLess(hHz(1), kHz(1))
		self.assertLess(kHz(1), MHz(1))
		self.assertLess(MHz(1), GHz(1))
		self.assertLess(GHz(1), THz(1))
		self.assertLess(THz(1), PHz(1))
		self.assertLess(PHz(1), EHz(1))
		# Frequency-to-Period
		self.assertLess(GHz(1), us(1))

	def test_comparison_le(self) -> None:
		# Frequency-to-Frequency
		self.assertLessEqual(aHz(1), fHz(1))
		self.assertLessEqual(fHz(1), pHz(1))
		self.assertLessEqual(pHz(1), nHz(1))
		self.assertLessEqual(nHz(1), uHz(1))
		self.assertLessEqual(uHz(1), mHz(1))
		self.assertLessEqual(mHz(1), cHz(1))
		self.assertLessEqual(cHz(1), dHz(1))
		self.assertLessEqual(dHz(1), Hz(1))
		self.assertLessEqual(Hz(1),  DHz(1))
		self.assertLessEqual(DHz(1), hHz(1))
		self.assertLessEqual(hHz(1), kHz(1))
		self.assertLessEqual(kHz(1), MHz(1))
		self.assertLessEqual(MHz(1), GHz(1))
		self.assertLessEqual(GHz(1), THz(1))
		self.assertLessEqual(THz(1), PHz(1))
		self.assertLessEqual(PHz(1), EHz(1))
		self.assertLessEqual(aHz(1), aHz(1))
		self.assertLessEqual(fHz(1), fHz(1))
		self.assertLessEqual(pHz(1), pHz(1))
		self.assertLessEqual(nHz(1), nHz(1))
		self.assertLessEqual(uHz(1), uHz(1))
		self.assertLessEqual(mHz(1), mHz(1))
		self.assertLessEqual(cHz(1), cHz(1))
		self.assertLessEqual(dHz(1), dHz(1))
		self.assertLessEqual(Hz(1),  Hz(1))
		self.assertLessEqual(DHz(1), DHz(1))
		self.assertLessEqual(hHz(1), hHz(1))
		self.assertLessEqual(kHz(1), kHz(1))
		self.assertLessEqual(MHz(1), MHz(1))
		self.assertLessEqual(GHz(1), GHz(1))
		self.assertLessEqual(THz(1), THz(1))
		self.assertLessEqual(PHz(1), PHz(1))
		# Frequency-to-Period
		self.assertLessEqual(GHz(1), us(1))
		self.assertLessEqual(GHz(1), ns(1))

	def test_comparison_eq(self) -> None:
		# Frequency-to-Frequency
		self.assertEqual(aHz(1), aHz(1))
		self.assertEqual(fHz(1), fHz(1))
		self.assertEqual(pHz(1), pHz(1))
		self.assertEqual(nHz(1), nHz(1))
		self.assertEqual(uHz(1), uHz(1))
		self.assertEqual(mHz(1), mHz(1))
		self.assertEqual(cHz(1), cHz(1))
		self.assertEqual(dHz(1), dHz(1))
		self.assertEqual(Hz(1),  Hz(1))
		self.assertEqual(DHz(1), DHz(1))
		self.assertEqual(hHz(1), hHz(1))
		self.assertEqual(kHz(1), kHz(1))
		self.assertEqual(MHz(1), MHz(1))
		self.assertEqual(GHz(1), GHz(1))
		self.assertEqual(THz(1), THz(1))
		self.assertEqual(PHz(1), PHz(1))
		# Frequency-to-Period
		self.assertEqual(GHz(1), ns(1))

	def test_comparison_ne(self) -> None:
		# Frequency-to-Frequency
		self.assertNotEqual(fHz(1), aHz(1))
		self.assertNotEqual(pHz(1), fHz(1))
		self.assertNotEqual(nHz(1), pHz(1))
		self.assertNotEqual(uHz(1), nHz(1))
		self.assertNotEqual(mHz(1), uHz(1))
		self.assertNotEqual(cHz(1), mHz(1))
		self.assertNotEqual(dHz(1), cHz(1))
		self.assertNotEqual(Hz(1),  dHz(1))
		self.assertNotEqual(DHz(1), Hz(1))
		self.assertNotEqual(hHz(1), DHz(1))
		self.assertNotEqual(kHz(1), hHz(1))
		self.assertNotEqual(MHz(1), kHz(1))
		self.assertNotEqual(GHz(1), MHz(1))
		self.assertNotEqual(THz(1), GHz(1))
		self.assertNotEqual(PHz(1), THz(1))
		self.assertNotEqual(EHz(1), PHz(1))
		# Frequency-to-Period
		self.assertNotEqual(GHz(1), ps(1))

	def test_comparison_gt(self) -> None:
		# Frequency-to-Frequency
		self.assertGreater(fHz(1), aHz(1))
		self.assertGreater(pHz(1), fHz(1))
		self.assertGreater(nHz(1), pHz(1))
		self.assertGreater(uHz(1), nHz(1))
		self.assertGreater(mHz(1), uHz(1))
		self.assertGreater(cHz(1), mHz(1))
		self.assertGreater(dHz(1), cHz(1))
		self.assertGreater(Hz(1),  dHz(1))
		self.assertGreater(DHz(1), Hz(1))
		self.assertGreater(hHz(1), DHz(1))
		self.assertGreater(kHz(1), hHz(1))
		self.assertGreater(MHz(1), kHz(1))
		self.assertGreater(GHz(1), MHz(1))
		self.assertGreater(THz(1), GHz(1))
		self.assertGreater(PHz(1), THz(1))
		self.assertGreater(EHz(1), PHz(1))
		# Frequency-to-Period
		self.assertGreater(GHz(1), ps(1))

	def test_comparison_ge(self) -> None:
		# Frequency-to-Frequency
		self.assertGreaterEqual(fHz(1), aHz(1))
		self.assertGreaterEqual(pHz(1), fHz(1))
		self.assertGreaterEqual(nHz(1), pHz(1))
		self.assertGreaterEqual(uHz(1), nHz(1))
		self.assertGreaterEqual(mHz(1), uHz(1))
		self.assertGreaterEqual(cHz(1), mHz(1))
		self.assertGreaterEqual(dHz(1), cHz(1))
		self.assertGreaterEqual(Hz(1),  dHz(1))
		self.assertGreaterEqual(DHz(1), Hz(1))
		self.assertGreaterEqual(hHz(1), DHz(1))
		self.assertGreaterEqual(kHz(1), hHz(1))
		self.assertGreaterEqual(MHz(1), kHz(1))
		self.assertGreaterEqual(GHz(1), MHz(1))
		self.assertGreaterEqual(THz(1), GHz(1))
		self.assertGreaterEqual(PHz(1), THz(1))
		self.assertGreaterEqual(EHz(1), PHz(1))
		self.assertGreaterEqual(fHz(1), fHz(1))
		self.assertGreaterEqual(pHz(1), pHz(1))
		self.assertGreaterEqual(nHz(1), nHz(1))
		self.assertGreaterEqual(uHz(1), uHz(1))
		self.assertGreaterEqual(mHz(1), mHz(1))
		self.assertGreaterEqual(cHz(1), cHz(1))
		self.assertGreaterEqual(dHz(1), dHz(1))
		self.assertGreaterEqual(Hz(1),  Hz(1))
		self.assertGreaterEqual(DHz(1), DHz(1))
		self.assertGreaterEqual(hHz(1), hHz(1))
		self.assertGreaterEqual(kHz(1), kHz(1))
		self.assertGreaterEqual(MHz(1), MHz(1))
		self.assertGreaterEqual(GHz(1), GHz(1))
		self.assertGreaterEqual(THz(1), THz(1))
		self.assertGreaterEqual(PHz(1), PHz(1))
		self.assertGreaterEqual(EHz(1), EHz(1))
		# Frequency-to-Period
		self.assertGreaterEqual(GHz(1), ps(1))
		self.assertGreaterEqual(GHz(1), ns(1))

	def test_comparison_wrong(self) -> None:
		with self.assertRaisesRegex(
			ToriiSyntaxError,
			r'^Comparison using \'>\' between a Torii Frequency and an object of the type \'int\' is not supported'
			r' \(test_time\.py, line \d+\)$'
		):
			_ = MHz(10) > 1

		with self.assertRaisesRegex(
			ToriiSyntaxError,
			r'^Comparison using \'<\' between a Torii Frequency and an object of the type \'float\' is not supported'
			r' \(test_time\.py, line \d+\)$'
		):
			_ = kHz(10) < 1.0

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

	def test_repr(self) -> None:
		self.assertEqual(f'{_as(50)!r}', '(period 50as)')
		self.assertEqual(f'{fs(50)!r}', '(period 50fs)')
		self.assertEqual(f'{ps(50)!r}', '(period 50ps)')
		self.assertEqual(f'{ns(50)!r}', '(period 50ns)')
		self.assertEqual(f'{us(50)!r}', '(period 50us)')
		self.assertEqual(f'{ms(50)!r}', '(period 50ms)')
		self.assertEqual(f'{cs(50)!r}', '(period 500ms)')
		self.assertEqual(f'{ds(5)!r}', '(period 500ms)')
		self.assertEqual(f'{s(50)!r}', '(period 50s)')
		self.assertEqual(f'{das(50)!r}', '(period 500s)')
		self.assertEqual(f'{hs(50)!r}', '(period 5ks)')
		self.assertEqual(f'{ks(50)!r}', '(period 50ks)')
		self.assertEqual(f'{Ms(50)!r}', '(period 50Ms)')
		self.assertEqual(f'{Gs(50)!r}', '(period 50Gs)')
		self.assertEqual(f'{Ts(50)!r}', '(period 50Ts)')
		self.assertEqual(f'{Ps(50)!r}', '(period 50Ps)')
		self.assertEqual(f'{Es(50)!r}', '(period 50Es)')

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

	def test_comparison_lt(self) -> None:
		# Period-to-Period
		self.assertLess(_as(1), fs(1))
		self.assertLess(fs(1), ps(1))
		self.assertLess(ps(1), ns(1))
		self.assertLess(ns(1), us(1))
		self.assertLess(us(1), ms(1))
		self.assertLess(ms(1), cs(1))
		self.assertLess(cs(1), ds(1))
		self.assertLess(ds(1), s(1))
		self.assertLess(s(1), das(1))
		self.assertLess(das(1), hs(1))
		self.assertLess(hs(1), ks(1))
		self.assertLess(ks(1), Ms(1))
		self.assertLess(Ms(1), Gs(1))
		self.assertLess(Gs(1), Ts(1))
		self.assertLess(Ts(1), Ps(1))
		self.assertLess(Ps(1), Es(1))
		# Period-to-Frequency
		self.assertLess(us(1), GHz(1))

	def test_comparison_le(self) -> None:
		# Period-to-Period
		self.assertLessEqual(_as(1), fs(1))
		self.assertLessEqual(fs(1), ps(1))
		self.assertLessEqual(ps(1), ns(1))
		self.assertLessEqual(ns(1), us(1))
		self.assertLessEqual(us(1), ms(1))
		self.assertLessEqual(ms(1), cs(1))
		self.assertLessEqual(cs(1), ds(1))
		self.assertLessEqual(ds(1), s(1))
		self.assertLessEqual(s(1), das(1))
		self.assertLessEqual(das(1), hs(1))
		self.assertLessEqual(hs(1), ks(1))
		self.assertLessEqual(ks(1), Ms(1))
		self.assertLessEqual(Ms(1), Gs(1))
		self.assertLessEqual(Gs(1), Ts(1))
		self.assertLessEqual(Ts(1), Ps(1))
		self.assertLessEqual(Ps(1), Es(1))
		self.assertLessEqual(_as(1), _as(1))
		self.assertLessEqual(fs(1),  fs(1))
		self.assertLessEqual(ps(1),  ps(1))
		self.assertLessEqual(ns(1),  ns(1))
		self.assertLessEqual(us(1),  us(1))
		self.assertLessEqual(ms(1),  ms(1))
		self.assertLessEqual(cs(1),  cs(1))
		self.assertLessEqual(ds(1),  ds(1))
		self.assertLessEqual(s(1),   s(1))
		self.assertLessEqual(das(1), das(1))
		self.assertLessEqual(hs(1),  hs(1))
		self.assertLessEqual(ks(1),  ks(1))
		self.assertLessEqual(Ms(1),  Ms(1))
		self.assertLessEqual(Gs(1),  Gs(1))
		self.assertLessEqual(Ts(1),  Ts(1))
		self.assertLessEqual(Ps(1),  Ps(1))
		# Period-to-Frequency
		self.assertLessEqual(us(1), GHz(1))
		self.assertLessEqual(ns(1), GHz(1))

	def test_comparison_eq(self) -> None:
		# Period-to-Period
		self.assertEqual(_as(1), _as(1))
		self.assertEqual(fs(1),  fs(1))
		self.assertEqual(ps(1),  ps(1))
		self.assertEqual(ns(1),  ns(1))
		self.assertEqual(us(1),  us(1))
		self.assertEqual(ms(1),  ms(1))
		self.assertEqual(cs(1),  cs(1))
		self.assertEqual(ds(1),  ds(1))
		self.assertEqual(s(1),   s(1))
		self.assertEqual(das(1), das(1))
		self.assertEqual(hs(1),  hs(1))
		self.assertEqual(ks(1),  ks(1))
		self.assertEqual(Ms(1),  Ms(1))
		self.assertEqual(Gs(1),  Gs(1))
		self.assertEqual(Ts(1),  Ts(1))
		self.assertEqual(Ps(1),  Ps(1))
		# Period-to-Frequency
		# self.assertEqual(ns(1), GHz(1)) # XXX(aki): Rounding issue

	def test_comparison_ne(self) -> None:
		# Period-to-Period
		self.assertNotEqual(_as(1), fs(1))
		self.assertNotEqual(fs(1), ps(1))
		self.assertNotEqual(ps(1), ns(1))
		self.assertNotEqual(ns(1), us(1))
		self.assertNotEqual(us(1), ms(1))
		self.assertNotEqual(ms(1), cs(1))
		self.assertNotEqual(cs(1), ds(1))
		self.assertNotEqual(ds(1), s(1))
		self.assertNotEqual(s(1), das(1))
		self.assertNotEqual(das(1), hs(1))
		self.assertNotEqual(hs(1), ks(1))
		self.assertNotEqual(ks(1), Ms(1))
		self.assertNotEqual(Ms(1), Gs(1))
		self.assertNotEqual(Gs(1), Ts(1))
		self.assertNotEqual(Ts(1), Ps(1))
		self.assertNotEqual(Ps(1), Es(1))
		# Period-to-Frequency
		self.assertNotEqual(ps(1), GHz(1))

	def test_comparison_gt(self) -> None:
		# Period-to-Period
		self.assertGreater(fs(1), _as(1))
		self.assertGreater(ps(1), fs(1))
		self.assertGreater(ns(1), ps(1))
		self.assertGreater(us(1), ns(1))
		self.assertGreater(ms(1), us(1))
		self.assertGreater(cs(1), ms(1))
		self.assertGreater(ds(1), cs(1))
		self.assertGreater(s(1), ds(1))
		self.assertGreater(das(1), s(1))
		self.assertGreater(hs(1), das(1))
		self.assertGreater(ks(1), hs(1))
		self.assertGreater(Ms(1), ks(1))
		self.assertGreater(Gs(1), Ms(1))
		self.assertGreater(Ts(1), Gs(1))
		self.assertGreater(Ps(1), Ts(1))
		self.assertGreater(Es(1), Ps(1))
		# Period-to-Frequency
		self.assertGreater(ps(1), GHz(1))

	def test_comparison_ge(self) -> None:
		# Period-to-Period
		self.assertGreater(fs(1), _as(1))
		self.assertGreater(ps(1), fs(1))
		self.assertGreater(ns(1), ps(1))
		self.assertGreater(us(1), ns(1))
		self.assertGreater(ms(1), us(1))
		self.assertGreater(cs(1), ms(1))
		self.assertGreater(ds(1), cs(1))
		self.assertGreater(s(1), ds(1))
		self.assertGreater(das(1), s(1))
		self.assertGreater(hs(1), das(1))
		self.assertGreater(ks(1), hs(1))
		self.assertGreater(Ms(1), ks(1))
		self.assertGreater(Gs(1), Ms(1))
		self.assertGreater(Ts(1), Gs(1))
		self.assertGreater(Ps(1), Ts(1))
		self.assertGreater(Es(1), Ps(1))
		self.assertGreaterEqual(_as(1), _as(1))
		self.assertGreaterEqual(fs(1),  fs(1))
		self.assertGreaterEqual(ps(1),  ps(1))
		self.assertGreaterEqual(ns(1),  ns(1))
		self.assertGreaterEqual(us(1),  us(1))
		self.assertGreaterEqual(ms(1),  ms(1))
		self.assertGreaterEqual(cs(1),  cs(1))
		self.assertGreaterEqual(ds(1),  ds(1))
		self.assertGreaterEqual(s(1),   s(1))
		self.assertGreaterEqual(das(1), das(1))
		self.assertGreaterEqual(hs(1),  hs(1))
		self.assertGreaterEqual(ks(1),  ks(1))
		self.assertGreaterEqual(Ms(1),  Ms(1))
		self.assertGreaterEqual(Gs(1),  Gs(1))
		self.assertGreaterEqual(Ts(1),  Ts(1))
		self.assertGreaterEqual(Ps(1),  Ps(1))
		# Period-to-Frequency
		self.assertGreaterEqual(ps(1), GHz(1))
		# self.assertGreaterEqual(ns(1), GHz(1)) # XXX(aki): Rounding issue

	def test_comparison_wrong(self) -> None:
		with self.assertRaisesRegex(
			ToriiSyntaxError,
			r'^Comparison using \'>\' between a Torii Period and an object of the type \'int\' is not supported'
			r' \(test_time\.py, line \d+\)$'
		):
			_ = s(10) > 1

		with self.assertRaisesRegex(
			ToriiSyntaxError,
			r'^Comparison using \'<\' between a Torii Period and an object of the type \'float\' is not supported'
			r' \(test_time\.py, line \d+\)$'
		):
			_ = ns(10) < 1.0
