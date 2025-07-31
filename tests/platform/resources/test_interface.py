# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.resources.interface import PCIBusResources, PCIeBusResources
from torii.test                         import ToriiTestCase

class PCIBusResourcesTestCase(ToriiTestCase):

	def test_base(self):
		resources = PCIBusResources(
			0,
			inta_n = 'X', intb_n = 'X', intc_n = 'X', intd_n = 'X',
			rst_n = 'X', clk = 'X', gnt_n = 'X', req_n = 'X', idsel = 'X',
			frame_n = 'X', irdy_n = 'X', trdy_n = 'X', devsel_n = 'X', stop_n = 'X',
			lock_n = 'X', perr_n = 'X', serr_n = 'X', smbclk = 'X', smbdat = 'X',
			ad_lower = 'X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X',
			cbe32_n = 'X X X X', par32 = 'X',
		)

		self.assertEqual(len(resources), 1)

		self.assertEqual(resources[0].name, 'pci_32')
		self.assertEqual(resources[0].number, 0)
		self.assertEqual(len(resources[0].ios), 22)

	def test_sub_busses(self):
		resources = PCIBusResources(
			0,
			inta_n = 'X', intb_n = 'X', intc_n = 'X', intd_n = 'X',
			rst_n = 'X', clk = 'X', gnt_n = 'X', req_n = 'X', idsel = 'X',
			frame_n = 'X', irdy_n = 'X', trdy_n = 'X', devsel_n = 'X', stop_n = 'X',
			lock_n = 'X', perr_n = 'X', serr_n = 'X', smbclk = 'X', smbdat = 'X',
			ad_lower = 'X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X',
			cbe32_n = 'X X X X', par32 = 'X',
			ad_upper = 'X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X',
			cbe64_n = 'X X X X', par64 = 'X', ack64_n = 'X', req64_n = 'X'
		)

		self.assertEqual(len(resources), 2)

		pci32 = resources[0]
		self.assertEqual(pci32.name, 'pci_32')
		self.assertEqual(pci32.number, 0)
		self.assertEqual(len(pci32.ios), 22)

		pci64 = resources[1]
		self.assertEqual(pci64.name, 'pci_64')
		self.assertEqual(pci64.number, 0)
		self.assertEqual(len(pci64.ios), 27)

class PCIeBusResourcesTestCase(ToriiTestCase):

	def test_base(self):
		resources = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G'
		)

		self.assertEqual(len(resources), 1)

		x1_bus = resources[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 4)

		x1_bus = PCIeBusResources(
			'test', 0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G'
		)[0]

		self.assertEqual(x1_bus.name, 'test_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 4)

		x1_bus = PCIeBusResources(
			5,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G'
		)[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 5)
		self.assertEqual(len(x1_bus.ios), 4)

	def test_optional(self):
		resources = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
			wake_n = 'H'
		)

		self.assertEqual(len(resources), 1)

		x1_bus = resources[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 5)

		x1_bus = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
			clkreq_n = 'H',
		)[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 5)

		x1_bus = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
			smdat = 'H', smclk = 'I'
		)[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 6)

		x1_bus = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
			tck = 'H', tdi = 'I', tdo = 'J', tms = 'K', trst_n = 'L'
		)[0]

		self.assertEqual(x1_bus.name, 'pcie_x1')
		self.assertEqual(x1_bus.number, 0)
		self.assertEqual(len(x1_bus.ios), 9)

	def test_sub_busses(self):
		resources = PCIeBusResources(
			0,
			perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
			# x1
			pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
			# x2
			pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
			# x4
			pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
			pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
			# x6
			pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
			pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
			# x8
			pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
			pet7_p = 'X', pet7_n = 'X', per7_p = 'X', per7_n = 'X',
			# x12
			pet8_p = 'X', pet8_n = 'X', per8_p = 'X', per8_n = 'X',
			pet9_p = 'X', pet9_n = 'X', per9_p = 'X', per9_n = 'X',
			pet10_p = 'X', pet10_n = 'X', per10_p = 'X', per10_n = 'X',
			pet11_p = 'X', pet11_n = 'X', per11_p = 'X', per11_n = 'X',
			# x16
			pet12_p = 'X', pet12_n = 'X', per12_p = 'X', per12_n = 'X',
			pet13_p = 'X', pet13_n = 'X', per13_p = 'X', per13_n = 'X',
			pet14_p = 'X', pet14_n = 'X', per14_p = 'X', per14_n = 'X',
			pet15_p = 'X', pet15_n = 'X', per15_p = 'X', per15_n = 'X',
			# x24
			pet16_p = 'X', pet16_n = 'X', per16_p = 'X', per16_n = 'X',
			pet17_p = 'X', pet17_n = 'X', per17_p = 'X', per17_n = 'X',
			pet18_p = 'X', pet18_n = 'X', per18_p = 'X', per18_n = 'X',
			pet19_p = 'X', pet19_n = 'X', per19_p = 'X', per19_n = 'X',
			pet20_p = 'X', pet20_n = 'X', per20_p = 'X', per20_n = 'X',
			pet21_p = 'X', pet21_n = 'X', per21_p = 'X', per21_n = 'X',
			pet22_p = 'X', pet22_n = 'X', per22_p = 'X', per22_n = 'X',
			pet23_p = 'X', pet23_n = 'X', per23_p = 'X', per23_n = 'X',
			# x32
			pet24_p = 'X', pet24_n = 'X', per24_p = 'X', per24_n = 'X',
			pet25_p = 'X', pet25_n = 'X', per25_p = 'X', per25_n = 'X',
			pet26_p = 'X', pet26_n = 'X', per26_p = 'X', per26_n = 'X',
			pet27_p = 'X', pet27_n = 'X', per27_p = 'X', per27_n = 'X',
			pet28_p = 'X', pet28_n = 'X', per28_p = 'X', per28_n = 'X',
			pet29_p = 'X', pet29_n = 'X', per29_p = 'X', per29_n = 'X',
			pet30_p = 'X', pet30_n = 'X', per30_p = 'X', per30_n = 'X',
			pet31_p = 'X', pet31_n = 'X', per31_p = 'X', per31_n = 'X',
		)

		self.assertEqual(len(resources), 9)

		x1 = resources[0]
		self.assertEqual(x1.name, 'pcie_x1')
		self.assertEqual(x1.number, 0)
		self.assertEqual(len(x1.ios), 4)

		x2 = resources[1]
		self.assertEqual(x2.name, 'pcie_x2')
		self.assertEqual(x2.number, 0)
		self.assertEqual(len(x2.ios), 6)

		x4 = resources[2]
		self.assertEqual(x4.name, 'pcie_x4')
		self.assertEqual(x4.number, 0)
		self.assertEqual(len(x4.ios), 10)

		x6 = resources[3]
		self.assertEqual(x6.name, 'pcie_x6')
		self.assertEqual(x6.number, 0)
		self.assertEqual(len(x6.ios), 14)

		x8 = resources[4]
		self.assertEqual(x8.name, 'pcie_x8')
		self.assertEqual(x8.number, 0)
		self.assertEqual(len(x8.ios), 18)

		x12 = resources[5]
		self.assertEqual(x12.name, 'pcie_x12')
		self.assertEqual(x12.number, 0)
		self.assertEqual(len(x12.ios), 26)

		x16 = resources[6]
		self.assertEqual(x16.name, 'pcie_x16')
		self.assertEqual(x16.number, 0)
		self.assertEqual(len(x16.ios), 34)

		x24 = resources[7]
		self.assertEqual(x24.name, 'pcie_x24')
		self.assertEqual(x24.number, 0)
		self.assertEqual(len(x24.ios), 50)

		x32 = resources[8]
		self.assertEqual(x32.name, 'pcie_x32')
		self.assertEqual(x32.number, 0)
		self.assertEqual(len(x32.ios), 66)

	def test_warnings(self):
		with self.assertWarnsRegex(
			ResourceWarning,
			r'^You specified a pwrbrk_n signal, however not enough PCIe lines for at least an x4 bus\. '
			r'Therefore pwrbrk was not used. Was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C', pwrbrk_n = 'D',
				pet0_p = 'E', pet0_n = 'F', per0_p = 'G', per0_n = 'H',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x2 signals were provided, was this intentional\? '
			r'This is an uncommon bus width, did you intend for a PCIe x4\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x4 signals were provided, was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x6 signals were provided, was this intentional\? '
			r'This is an uncommon bus width, did you intend for a PCIe x8\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x8 signals were provided, was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
				pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
				pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x12 signals were provided, was this intentional\? '
			r'This is an uncommon bus width, did you intend for a PCIe x16\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
				pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
				pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
				pet7_p = 'X', pet7_n = 'X', per7_p = 'X', per7_n = 'X',
				pet8_p = 'X', pet8_n = 'X', per8_p = 'X', per8_n = 'X',
				pet9_p = 'X', pet9_n = 'X', per9_p = 'X', per9_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x16 signals were provided, was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
				pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
				pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
				pet7_p = 'X', pet7_n = 'X', per7_p = 'X', per7_n = 'X',
				pet8_p = 'X', pet8_n = 'X', per8_p = 'X', per8_n = 'X',
				pet9_p = 'X', pet9_n = 'X', per9_p = 'X', per9_n = 'X',
				pet10_p = 'X', pet10_n = 'X', per10_p = 'X', per10_n = 'X',
				pet11_p = 'X', pet11_n = 'X', per11_p = 'X', per11_n = 'X',
				pet12_p = 'X', pet12_n = 'X', per12_p = 'X', per12_n = 'X',
				pet13_p = 'X', pet13_n = 'X', per13_p = 'X', per13_n = 'X',
				pet14_p = 'X', pet14_n = 'X', per14_p = 'X', per14_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x24 signals were provided, was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
				pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
				pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
				pet7_p = 'X', pet7_n = 'X', per7_p = 'X', per7_n = 'X',
				pet8_p = 'X', pet8_n = 'X', per8_p = 'X', per8_n = 'X',
				pet9_p = 'X', pet9_n = 'X', per9_p = 'X', per9_n = 'X',
				pet10_p = 'X', pet10_n = 'X', per10_p = 'X', per10_n = 'X',
				pet11_p = 'X', pet11_n = 'X', per11_p = 'X', per11_n = 'X',
				pet12_p = 'X', pet12_n = 'X', per12_p = 'X', per12_n = 'X',
				pet13_p = 'X', pet13_n = 'X', per13_p = 'X', per13_n = 'X',
				pet14_p = 'X', pet14_n = 'X', per14_p = 'X', per14_n = 'X',
				pet15_p = 'X', pet15_n = 'X', per15_p = 'X', per15_n = 'X',
				pet16_p = 'X', pet16_n = 'X', per16_p = 'X', per16_n = 'X',
				pet17_p = 'X', pet17_n = 'X', per17_p = 'X', per17_n = 'X',
				pet18_p = 'X', pet18_n = 'X', per18_p = 'X', per18_n = 'X',
				pet19_p = 'X', pet19_n = 'X', per19_p = 'X', per19_n = 'X',
				pet20_p = 'X', pet20_n = 'X', per20_p = 'X', per20_n = 'X',
				pet21_p = 'X', pet21_n = 'X', per21_p = 'X', per21_n = 'X',
			)

		with self.assertWarnsRegex(
			ResourceWarning,
			r'^Only a subset of the PCIe x32 signals were provided, was this intentional\?$'
		):
			PCIeBusResources(
				0,
				perst_n = 'A', refclk_p = 'B', refclk_n = 'C',
				pet0_p = 'D', pet0_n = 'E', per0_p = 'F', per0_n = 'G',
				pet1_p = 'X', pet1_n = 'X', per1_p = 'X', per1_n = 'X',
				pet2_p = 'X', pet2_n = 'X', per2_p = 'X', per2_n = 'X',
				pet3_p = 'X', pet3_n = 'X', per3_p = 'X', per3_n = 'X',
				pet4_p = 'X', pet4_n = 'X', per4_p = 'X', per4_n = 'X',
				pet5_p = 'X', pet5_n = 'X', per5_p = 'X', per5_n = 'X',
				pet6_p = 'X', pet6_n = 'X', per6_p = 'X', per6_n = 'X',
				pet7_p = 'X', pet7_n = 'X', per7_p = 'X', per7_n = 'X',
				pet8_p = 'X', pet8_n = 'X', per8_p = 'X', per8_n = 'X',
				pet9_p = 'X', pet9_n = 'X', per9_p = 'X', per9_n = 'X',
				pet10_p = 'X', pet10_n = 'X', per10_p = 'X', per10_n = 'X',
				pet11_p = 'X', pet11_n = 'X', per11_p = 'X', per11_n = 'X',
				pet12_p = 'X', pet12_n = 'X', per12_p = 'X', per12_n = 'X',
				pet13_p = 'X', pet13_n = 'X', per13_p = 'X', per13_n = 'X',
				pet14_p = 'X', pet14_n = 'X', per14_p = 'X', per14_n = 'X',
				pet15_p = 'X', pet15_n = 'X', per15_p = 'X', per15_n = 'X',
				pet16_p = 'X', pet16_n = 'X', per16_p = 'X', per16_n = 'X',
				pet17_p = 'X', pet17_n = 'X', per17_p = 'X', per17_n = 'X',
				pet18_p = 'X', pet18_n = 'X', per18_p = 'X', per18_n = 'X',
				pet19_p = 'X', pet19_n = 'X', per19_p = 'X', per19_n = 'X',
				pet20_p = 'X', pet20_n = 'X', per20_p = 'X', per20_n = 'X',
				pet21_p = 'X', pet21_n = 'X', per21_p = 'X', per21_n = 'X',
				pet22_p = 'X', pet22_n = 'X', per22_p = 'X', per22_n = 'X',
				pet23_p = 'X', pet23_n = 'X', per23_p = 'X', per23_n = 'X',
				pet24_p = 'X', pet24_n = 'X', per24_p = 'X', per24_n = 'X',
				pet25_p = 'X', pet25_n = 'X', per25_p = 'X', per25_n = 'X',
				pet26_p = 'X', pet26_n = 'X', per26_p = 'X', per26_n = 'X',
				pet27_p = 'X', pet27_n = 'X', per27_p = 'X', per27_n = 'X',
				pet28_p = 'X', pet28_n = 'X', per28_p = 'X', per28_n = 'X',
			)
