from ...core.cpu import Cpu
from ...core.types import I2cAddr, PciAddr

from ...components.cpu.amd.k10temp import K10Temp
from ...components.lm75 import Tmp75

from ...descs.sensor import Position, SensorDesc

class PrairieCpu(Cpu):

   PLATFORM = 'prairie'

   def __init__(self, tempBus=1, **kwargs):
      super().__init__(**kwargs)

      self.newComponent(K10Temp, addr=PciAddr(device=0x18, func=3), sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=70, overheat=95, critical=115),
      ])

      self.newComponent(Tmp75, addr=I2cAddr(bus=tempBus, address=0x4A), sensors=[
         SensorDesc(diode=0, name='Psu temp sensor',
                    position=Position.INLET, overheat=75, critical=80),
      ])

      self.newComponent(Tmp75, addr=I2cAddr(bus=tempBus, address=0x4B), sensors=[
         SensorDesc(diode=0, name='SFP+ connector temp sensor',
                    position=Position.OTHER, overheat=75, critical=80),
      ])

      self.newComponent(Tmp75, addr=I2cAddr(bus=tempBus, address=0x4C), sensors=[
         SensorDesc(diode=0, name='MAC external temp sensor',
                    position=Position.OTHER, overheat=75, critical=80),
      ])
