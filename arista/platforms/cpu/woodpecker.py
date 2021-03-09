from ...core.cpu import Cpu
from ...core.fan import FanSlot
from ...core.types import PciAddr
from ...core.utils import incrange

from ...components.cpu.amd.k10temp import K10Temp
from ...components.dpm.ucd import Ucd90160, UcdGpi, UcdPriority
from ...components.max6658 import Max6658
from ...components.scd import Scd

from ...descs.fan import FanDesc, FanPosition
from ...descs.led import LedDesc, LedColor
from ...descs.sensor import Position, SensorDesc

class WoodpeckerCpu(Cpu):

   PLATFORM = 'woodpecker'

   def __init__(self, **kwargs):
      super(WoodpeckerCpu, self).__init__(**kwargs)

      self.newComponent(K10Temp, addr=PciAddr(device=0x18, func=3), sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=70, overheat=95, critical=115),
      ])

      cpld = self.newComponent(Scd, PciAddr(bus=0x00, device=0x09, func=0))
      self.cpld = cpld

      cpld.addFanGroup(0x9000, 3, 3)

      for i, slotId in enumerate(incrange(1, 3)):
         fanIn = FanDesc(fanId=i * 2 + 1, position=FanPosition.INLET)
         fanOut = FanDesc(fanId=i * 2 + 2, position=FanPosition.OUTLET)
         led = LedDesc(name='fan%d' % slotId,
                       colors=[LedColor.GREEN, LedColor.RED, LedColor.OFF])
         self.newComponent(
            FanSlot,
            slotId=slotId,
            led=cpld.addFanLed(led),
            fans=[
               cpld.addFan(fanIn),
               cpld.addFan(fanOut),
            ]
         )

      cpld.addSmbusMasterRange(0x8000, 2, 0x80, 4)
      cpld.newComponent(Max6658, cpld.i2cAddr(0, 0x4c), sensors=[
         SensorDesc(diode=0, name='CPU board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=85),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=55, overheat=75, critical=85),
      ])

      cpld.createPowerCycle()

   def addCpuDpm(self, addr=None, causes=None):
      addr = addr or self.cpuDpmAddr()
      return self.cpld.newComponent(Ucd90160, addr=addr, causes=causes or {
         'fansmissing': UcdGpi(5),
         'overtemp': UcdGpi(6),
         'procerror': UcdGpi(7, priority=UcdPriority.LOW),
      })

   def cpuDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x11, t=3, **kwargs):
      return self.cpld.i2cAddr(5, addr, t=t, **kwargs)
