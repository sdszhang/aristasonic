from ...core.cpu import Cpu
from ...core.fan import FanSlot
from ...core.types import I2cAddr
from ...core.utils import incrange

from ...components.cpu.amd.k10temp import K10Temp
from ...components.cpu.crow import (
   CrowCpldRegisters,
   CrowFanCpld,
   CrowSysCpld,
)
from ...components.max6658 import Max6658

from ...descs.fan import FanDesc, FanPosition
from ...descs.led import LedDesc, LedColor
from ...descs.sensor import Position, SensorDesc

class CrowCpu(Cpu):

   PLATFORM = 'crow'

   def __init__(self, scd, registerCls=CrowCpldRegisters, hwmonBus=0, **kwargs):
      super(CrowCpu, self).__init__(**kwargs)

      self.newComponent(K10Temp, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=60, overheat=90, critical=95),
      ])

      scd.newComponent(Max6658, scd.i2cAddr(hwmonBus, 0x4c), sensors=[
         SensorDesc(diode=0, name='Cpu board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=80),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=50, overheat=75, critical=85),
      ])

      cpld = scd.newComponent(CrowFanCpld, addr=scd.i2cAddr(hwmonBus, 0x60))
      for slotId in incrange(1, 4):
         fanDesc = FanDesc(fanId=slotId, position=FanPosition.INLET)
         ledDesc = LedDesc(name='fan%d' % slotId,
                           colors=[LedColor.RED, LedColor.GREEN, LedColor.OFF])
         self.newComponent(
            FanSlot,
            slotId=slotId,
            led=cpld.addFanLed(ledDesc),
            fans=[
               cpld.addFan(fanDesc),
            ]
         )

      self.syscpld = self.newComponent(CrowSysCpld, I2cAddr(1, 0x23),
                                       registerCls=registerCls)
      self.syscpld.createPowerCycle()
