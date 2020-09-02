
from __future__ import absolute_import, division

from ...components.denali.supervisor import DenaliSupervisor
from ...components.dpm import Ucd90120A, Ucd90160, UcdMon, UcdGpi
from ...components.eeprom import PrefdlSeeprom
from ...components.microsemi import MicrosemiPortDesc

from ...core.platform import registerPlatform
from ...core.types import PciAddr

from ...descs.gpio import GpioDesc

from ..cpu.sprucefish import SprucefishCpu

@registerPlatform()
class OtterLake(DenaliSupervisor):

   PLATFORM = 'sprucefish'
   SID = ['Otterlake']
   SKU = ['DCS-7800-SUP']

   LINECARD_PORTS = [
      MicrosemiPortDesc(32, 8, 0),
      MicrosemiPortDesc(33, 9, 0),
      MicrosemiPortDesc(34, 10, 0),
      MicrosemiPortDesc(35, 11, 0),
      MicrosemiPortDesc(36, 12, 0),
      MicrosemiPortDesc(37, 13, 0),
      MicrosemiPortDesc(38, 14, 0),
      MicrosemiPortDesc(39, 15, 0),
   ]

   FABRIC_PORTS = [
      MicrosemiPortDesc(24, 1, 0),
      MicrosemiPortDesc(25, 2, 0),
      MicrosemiPortDesc(26, 3, 0),
      MicrosemiPortDesc(27, 4, 0),
      MicrosemiPortDesc(28, 5, 0),
      MicrosemiPortDesc(29, 6, 0),
   ]

   ALL_PSUS = [(1, p) for p in range(7)] + [(2, p) for p in range(6)]

   def __init__(self, chassis=None, slot=None, **kwargs):
      super(OtterLake, self).__init__(chassis=chassis, slot=slot,
                                      scdAddr=PciAddr(bus=0x9f), **kwargs)

      self.cpu = None
      self.createCpuCard()
      self.createPsus()

   def createCpuCard(self):
      self.cpu = self.newComponent(SprucefishCpu)

      self.cpu.cpld.newComponent(Ucd90160, self.cpu.cpuDpmAddr())
      self.cpu.cpld.newComponent(Ucd90120A, self.cpu.shimDpmAddr(), causes={
         'peer': UcdGpi(4),
         'reboot': UcdGpi(5),
         'watchdog': UcdGpi(6),
         'powerloss': UcdMon(9),
      })

      self.eeprom = self.cpu.cpld.newComponent(PrefdlSeeprom,
                                               self.cpu.shimEepromAddr())

   def createPsus(self):
      for idx, (bankId, psuId) in enumerate(self.ALL_PSUS):
         name = "bank%d_psu%d" % (bankId, psuId + 1)
         self.scd.addGpios([
            GpioDesc("%s_present" % name, 0x5080, idx, ro=True),
            GpioDesc("%s_present_changed" % name, 0x5080, 16 + idx),
            GpioDesc("%s_ok" % name, 0x5090, idx, ro=True),
            GpioDesc("%s_ok_changed" % name, 0x5090, 16 + idx),
            GpioDesc("%s_ac_a_ok" % name, 0x50A0, idx, ro=True),
            GpioDesc("%s_ac_a_ok_changed" % name, 0x50A0, 16 + idx),
            GpioDesc("%s_ac_b_ok" % name, 0x50B0, idx, ro=True),
            GpioDesc("%s_ac_b_ok_changed" % name, 0x50B0, 16 + idx),
         ])

         # TODO: PSU smbus
