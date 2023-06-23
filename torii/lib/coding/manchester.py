# SPDX-License-Identifier: BSD-2-Clause

from ...hdl import Elaboratable, Signal, Module

__all__ = (
	'Encoder',
	'Decoder',
)

class Encoder(Elaboratable):

	def __init__(self) -> None:
		self.data_in  = Signal()
		self.step     = Signal()
		self.data_out = Signal(reset = 1)
		self.bypass   = Signal()

	def elaborate(self, _) -> Module:
		m = Module()

		data  = Signal()
		cycle = Signal()

		with m.If(self.step):
			with m.If(self.bypass):
				m.d.sync += [
					self.data_out.eq(self.data_in),
					cycle.eq(0)
				]
			with m.Elif(~cycle):
				m.d.sync += [
					data.eq(self.data_in),
					self.data_out.eq(self.data_in),
					cycle.eq(1)
				]
			with m.Else():
				m.d.sync += [
					self.data_out.eq(~data),
					cycle.eq(0)
				]

		return m

class Decoder(Elaboratable):

	def __init__(self) -> None:
		self.data_in  = Signal()
		self.step     = Signal()
		self.data_out = Signal()
		self.valid    = Signal()
		self.bypass   = Signal()

	def elaborate(self, _) -> Module:
		m = Module()

		data  = Signal()
		cycle = Signal()

		with m.If(self.step):
			with m.If(~cycle):
				m.d.sync += [
					data.eq(self.data_in),
					cycle.eq(1),
				]
			with m.Elif(~self.bypass):
				m.d.sync += [
					self.data_out.eq(data),
					self.valid.eq(data == ~self.data_in),
					cycle.eq(0)
				]
			with m.Else():
				m.d.sync += [
					self.data_out.eq(data),
					self.valid.eq(data == self.data_in),
					cycle.eq(0)
				]

		return m
