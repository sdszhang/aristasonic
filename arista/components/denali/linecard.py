
from __future__ import absolute_import, division, print_function

import time

from .card import DenaliCard, DenaliCardSlot
from ..asic.dnx.jericho2 import Jericho2
from ..linecard import Linecard
from ..plx import PlxPex8700
from ..scd import Scd
from ...core.provision import ProvisionConfig, ProvisionMode
from ...core.register import RegBitField, RegisterMap
from ...core.types import PciAddr
from ...drivers.pca9555 import GpioRegister
from ...drivers.scd.register import ScdResetRegister
from ...drivers.scd.sram import SramContent
from ...libs.wait import waitFor

class DenaliLinecard(DenaliCard, Linecard):
   PLATFORM = None

   SCD_PCI_OFFSET = 0
   ASIC_PCI_OFFSET = {}

   PLX_LCPU_MODE = None

   def createPlx(self):
      self.plx = self.standby.newComponent(PlxPex8700,
                                           addr=self.slot.bus.i2cAddr(0x38))

   def createScd(self):
      scdAddr = self.slot.pciAddr(bus=self.SCD_PCI_OFFSET)
      self.scd = self.main.newComponent(Scd, scdAddr, registerCls=ScdRegisterMap)

   def createAsics(self):
      asicAddr = self.slot.pciAddr(bus=self.ASIC_PCI_OFFSET[0])
      self.asics = [
         self.main.newComponent(Jericho2, asicAddr, rescan=True,
                                resetGpio=self.scd.regs.je1Reset,
                                pcieResetGpio=self.scd.regs.je1PcieReset),
      ]

   def createCpu(self):
      assert self.CPU_CLS
      self.slot = DenaliCardSlot(self, 0, PciAddr(bus=0x04), None, card=self)
      self.cpu = self.newComponent(self.CPU_CLS, self.slot)

   def powerStandbyDomainIs(self, on):
      '''Turn on card Ecbs. On Denali linecard, we expect
         Dpms will then be turned on as well as Pols by hardware. So no need to
         do anything with Dpm. When all is done, power good is asserted.'''
      assert self.gpio1, "gpio1 is not created yet."
      if on:
         self.gpio1.cpEcbOn(True)
         self.gpio1.dpEcbOn(True)
         self.gpio1.scdReset(False)
         self.gpio1.pcieUpstream(False)
         waitFor(self.poweredOn, "Card failed to be turned on.")
      else:
         self.gpio1.cpEcbOn(False)
         self.gpio1.dpEcbOn(False)
         self.gpio1.scdReset(True)
         self.gpio1.pcieUpstream(True)
         # In Denali fabric card, we should not turn off Ecb fans
         waitFor(lambda: (not self.poweredOn()), "Card failed to be turned off.")

   def populateSramFromPrefdl(self):
      sramContent = SramContent()
      prefdlRaw = self.eeprom.read()
      for addr, byte in enumerate(prefdlRaw):
         sramContent.write(addr, byte)
      self.syscpld.sram(sramContent)

   def provisionIs(self, provisionStatus):
      config = ProvisionConfig(self.slot.slotId)
      if provisionStatus is None:
         provisionStatus = config.loadMode()
      else:
         config.writeMode(provisionStatus)
      self.syscpld.provision(provisionStatus)

   def powerLcpuIs(self, on, lcpuCtx):
      if on:
         assert self.syscpld.lcpuInReset(), "LCPU should be in reset"
         self.gpio1.lcpuMode(True)
         self.syscpld.slotId(self.slot.slotId)
         self.provisionIs(lcpuCtx.provision)
         self.populateSramFromPrefdl()
         self.syscpld.gmacLowPower(False)
         self.syscpld.supGmacReset(False)
         self.syscpld.lcpuGmacReset(False)
         self.syscpld.lcpuDisableSet(False)
         self.syscpld.lcpuResetSet(False)
         waitFor(self.syscpld.lcpuPowerGood, "LCPU power to be good")
         # This is rather ugly, but seems to be necessary to avoid any issues with
         # the tg3 driver for the SUP GMAC. With a shorter sleep, or no sleep at all
         # we sometimes experience TX transmit timeouts during the lifetime of the
         # linecard. This sleep seems to completely remove this issue. Time will tell
         # if it's a real fix for that, but so far looks necessary. Sleeping 4
         # seconds or more also seem to not show up the tg3_abort_hw timed out error
         # at power on time.
         #
         # Unfortunately for now I can't think of a better fix than sleep. I don't
         # think we can wait on anything...
         time.sleep(4)
      else:
         self.syscpld.lcpuResetSet(True)
         self.syscpld.lcpuDisableSet(True)
         self.syscpld.lcpuGmacReset(True)
         self.syscpld.supGmacReset(True)
         self.syscpld.gmacLowPower(True)
         self.syscpld.provision(ProvisionMode.NONE)
         self.syscpld.slotId(0)
         self.gpio1.lcpuMode(False)
         waitFor(lambda: (not self.syscpld.lcpuPowerGood()),
                 "LCPU power to be turned off")

   def setupPlxLcpuMode(self):
      if self.PLX_LCPU_MODE:
         self.plx.vsPortVec(0, self.PLX_LCPU_MODE[0])
         self.plx.vsPortVec(1, self.PLX_LCPU_MODE[1])

   def setupPlx(self):
      self.enablePlxDownstreamHotplug()
      self.setupPlxLcpuMode()

class GpioRegisterMap(RegisterMap):
   BANK0 = GpioRegister(0x0,
      RegBitField(1, 'tempAlert', flip=True),
      RegBitField(2, 'powerGood'),
      RegBitField(4, 'powerCycle', ro=False),
      RegBitField(7, 'pcieFatalError', flip=True),
   )
   BANK1 = GpioRegister(0x1,
      RegBitField(0, 'cpEcbOn', ro=False),
      RegBitField(1, 'dpEcbOn', ro=False),
      RegBitField(2, 'statusGrn', ro=False, flip=True),
      RegBitField(3, 'statusRed', ro=False, flip=True),
      RegBitField(4, 'pcieUpstream', ro=False),
      RegBitField(5, 'lcpuMode', ro=False),
      RegBitField(6, 'pcieReset', ro=False, flip=True),
      RegBitField(7, 'scdReset', ro=False, flip=True),
   )

class ScdRegisterMap(RegisterMap):
   RESET0 = ScdResetRegister(0x4000,
      RegBitField(0, 'je0Reset', ro=False),
      RegBitField(1, 'je0PcieReset', ro=False),
      RegBitField(2, 'je1Reset', ro=False),
      RegBitField(3, 'je1PcieReset', ro=False),
      RegBitField(4, 'je2Reset', ro=False),
      RegBitField(5, 'je2PcieReset', ro=False),
   )
