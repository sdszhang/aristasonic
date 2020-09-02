from ...core.cpu import Cpu
from ...core.register import Register, RegisterMap
from ...core.types import I2cAddr, PciAddr

from ...components.eeprom import PrefdlSeeprom
from ...components.scd import Scd

class HedgehogCpuCpld(RegisterMap):
   REVISION = Register(0x10, name='revision')
   SCRATCHPAD = Register(0x20, name='scratchpad', ro=False)
   SLOT_ID = Register(0x30, name='slotId')
   PROVISION = Register(0x50, name='provision')

class HedgehogCpu(Cpu):

   PLATFORM = 'hedgehog'

   def __init__(self, slot, **kwargs):
      super(HedgehogCpu, self).__init__(**kwargs)
      self.slot = slot
      self.eeprom = self.newComponent(PrefdlSeeprom, I2cAddr(1, 0x50))
      self.syscpld = self.newComponent(Scd, PciAddr(bus=0, device=0x18, func=7),
                                       registerCls=HedgehogCpuCpld)
