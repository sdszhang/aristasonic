from ...core.cpu import Cpu
from ...core.types import PciAddr

from ...components.dpm.adm1266 import Adm1266, AdmPin, AdmPriority
from ...components.scd import Scd

class LorikeetCpu(Cpu):

   PLATFORM = 'lorikeet'

   def __init__(self, addr=PciAddr(device=0x18, func=7), **kwargs):
      super(LorikeetCpu, self).__init__(**kwargs)

      self.cpld = self.newComponent(Scd, addr=addr)

      self.cpld.createInterrupt(addr=0x3000, num=0)

      self.cpld.addLeds([
         (0x4000, 'beacon'),
         (0x4010, 'status'),
         (0x4020, 'fan_status'),
         (0x4030, 'psu1'),
         (0x4040, 'psu2'),
      ])

      self.cpld.createPowerCycle()
      self.cpld.addSmbusMasterRange(0x8000, 2, 0x80, 4)
      self.cpld.addFanGroup(0x9000, 3, 3)

      # TODO: Add MAX6658 and ISL69247 temp sensors

   def addCpuDpm(self, addr=None, causes=None):
      addr = addr or self.cpuDpmAddr()
      return self.cpld.newComponent(Adm1266, addr=addr, causes=causes or {
         'fansmissing': AdmPin(5, AdmPin.GPIO),
         'overtemp': AdmPin(6, AdmPin.GPIO),
         'procerror': AdmPin(7, AdmPin.GPIO, priority=AdmPriority.LOW),
      })

   def cpuDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(5, addr, t=t, **kwargs)
