from ...core.cpu import Cpu
from ...core.types import PciAddr

from ...components.cpu.amd.k10temp import K10Temp

from ...descs.sensor import Position, SensorDesc

class NewportCpu(Cpu):

   PLATFORM = 'newport'

   def __init__(self, **kwargs):
      super().__init__(**kwargs)

      self.newComponent(K10Temp, addr=PciAddr(device=0x18, func=3), sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=60, overheat=105, critical=115),
      ])
