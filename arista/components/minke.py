from ..components.lm75 import Tmp75

from ..core.component.i2c import I2cComponent
from ..core.component import Priority
from ..core.fan import FanSlot

from ..descs.fan import FanDesc, FanPosition
from ..descs.led import LedDesc, LedColor
from ..descs.sensor import Position, SensorDesc

from ..drivers.minke import MinkeFanCpldKernelDriver

from .eeprom import At24C32

class MinkeFanCpld(I2cComponent):
   DRIVER = MinkeFanCpldKernelDriver
   PRIORITY = Priority.COOLING

class Minke:

   FAN_SLOTS = 3
   FAN_COUNT = 6

   def __init__(self, parent, bus):
      parent.newComponent(Tmp75, addr=bus.i2cAddr(0x48), sensors=[
         SensorDesc(diode=0, name='Outlet', position=Position.OUTLET,
            target=65, overheat=80, critical=95),
      ])
      self.eeprom = parent.newComponent(At24C32, addr=bus.i2cAddr(0x50))

      self.cpld = parent.newComponent(MinkeFanCpld, addr=bus.i2cAddr(0x60))

      for slotId in range(1, self.FAN_SLOTS + 1):
         parent.newComponent(
            FanSlot,
            slotId=slotId,
            led=self.cpld.addFanLed(LedDesc(
               name='fan_slot%d' % slotId,
               colors=[LedColor.RED, LedColor.AMBER, LedColor.GREEN,
                       LedColor.BLUE, LedColor.OFF],
            )),
            fans=[self.cpld.addFan(desc) for desc in [
               FanDesc(fanId=slotId * 2 - 1, position=FanPosition.INLET),
               FanDesc(fanId=slotId * 2, position=FanPosition.INLET),
            ]],
         )
