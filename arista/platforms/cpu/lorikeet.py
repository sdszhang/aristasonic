from ...core.cpu import Cpu
from ...core.types import PciAddr

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

      # TODO: Add ADM1266 DPM
      # TODO: Add MAX6658 and ISL69247 temp sensors
