from ...core.cpu import Cpu
from ...core.types import I2cAddr
from ...core.utils import incrange

from ...components.cpu.amd.k10temp import K10Temp
from ...components.cpu.crow import CrowSysCpld, CrowFanCpldComponent
from ...components.max6658 import Max6658

from ...descs.fan import FanDesc
from ...descs.sensor import Position, SensorDesc

class CrowCpu(Cpu):

   PLATFORM = 'crow'

   def __init__(self, scd, hwmonOffset=2, **kwargs):
      super(CrowCpu, self).__init__(**kwargs)

      self.newComponent(K10Temp, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=60, overheat=90, critical=95),
      ])

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon%d' % hwmonOffset,
                       sensors=[
         SensorDesc(diode=0, name='Cpu board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=80),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=50, overheat=75, critical=85),
      ])

      scd.newComponent(CrowFanCpldComponent, addr=scd.i2cAddr(0, 0x60),
                       waitFile='/sys/class/hwmon/hwmon%d' % (hwmonOffset + 1),
                       fans=[
         FanDesc(fanId) for fanId in incrange(1, 4)
      ])

      self.syscpld = self.newComponent(CrowSysCpld, I2cAddr(1, 0x23))
      self.syscpld.createPowerCycle()
