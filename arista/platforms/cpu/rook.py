from ...core.cpu import Cpu
from ...core.types import PciAddr
from ...core.utils import incrange

from ...components.coretemp import Coretemp
from ...components.cpu.intel.pch import Pch
from ...components.cpu.rook import RookStatusLeds, RookSysCpld, RookCpldRegisters
from ...components.lm73 import Lm73
from ...components.max6658 import Max6658
from ...components.scd import Scd

from ...descs.fan import FanDesc
from ...descs.led import LedDesc
from ...descs.sensor import Position, SensorDesc

class RookCpu(Cpu):

   PLATFORM = 'rook'

   def __init__(self, fanCount=4, fanCpldCls=None, mgmtBus=15,
                cpldRegisterCls=RookCpldRegisters, **kwargs):
      super(RookCpu, self).__init__(**kwargs)

      self.newComponent(Pch, sensors=[
         SensorDesc(diode=0, name='PCH temp sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
      ])

      self.newComponent(Coretemp, sensors=[
         SensorDesc(diode=0, name='Physical id 0',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
         SensorDesc(diode=1, name='CPU core0 temp sensor',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
         SensorDesc(diode=2, name='CPU core1 temp sensor',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
      ])

      cpld = self.newComponent(Scd, PciAddr(bus=0xff, device=0x0b, func=3))
      self.cpld = cpld

      cpld.addSmbusMasterRange(0x8000, 4, 0x80, 4)
      cpld.newComponent(Max6658, cpld.i2cAddr(0, 0x4c), sensors=[
         SensorDesc(diode=0, name='CPU board temp sensor',
                    position=Position.OTHER, target=70, overheat=80, critical=85),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=55, overheat=65, critical=75),
      ])

      cpld.newComponent(fanCpldCls, cpld.i2cAddr(12, 0x60), fans=[
         FanDesc(fanId) for fanId in incrange(1, fanCount)
      ])

      cpld.newComponent(Lm73, cpld.i2cAddr(mgmtBus, 0x48), sensors=[
         SensorDesc(diode=0, name='Front-panel temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=85),
      ])

      self.leds = cpld.newComponent(RookStatusLeds, cpld.i2cAddr(mgmtBus, 0x20),
                                    leds=[
         LedDesc(name='beacon', colors=['blue']),
         LedDesc(name='fan_status', colors=['green', 'red']),
         LedDesc(name='psu1_status', colors=['green', 'red']),
         LedDesc(name='psu2_status', colors=['green', 'red']),
         LedDesc(name='status', colors=['green', 'red']),
      ])

      cpld.createPowerCycle()

      self.syscpld = self.newComponent(RookSysCpld, cpld.i2cAddr(8, 0x23),
                                       registerCli=cpldRegisterCls)

   def cpuDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(10, addr, t=t, **kwargs)
