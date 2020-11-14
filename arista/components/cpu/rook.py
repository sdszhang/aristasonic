
from ...accessors.led import LedImpl

from ...core.log import getLogger
from ...core.register import Register, RegBitField

from ...drivers.rook import (
   RookLedSysfsDriver,
   RookFanCpldKernelDriver,
   RookStatusLedKernelDriver,
)

from ..common import I2cComponent
from ..cpld import SysCpld, SysCpldCommonRegisters

logging = getLogger(__name__)

class RookCpldRegisters(SysCpldCommonRegisters):
   INTERRUPT_STS = Register(0x08,
      RegBitField(0, 'scdCrcError'),
   )
   SCD_CTRL_STS = Register(0x0A,
      RegBitField(0, 'scdConfDone'),
      RegBitField(1, 'scdInitDone'),
      RegBitField(5, 'scdReset', ro=False),
   )
   PWR_CYC_EN = Register(0x17,
      RegBitField(0, 'powerCycleOnCrc', ro=False),
   )

class RookSysCpld(SysCpld):
   def __init__(self, addr, drivers=None, registerCls=RookCpldRegisters, **kwargs):
      super(RookSysCpld, self).__init__(addr=addr, drivers=drivers,
                                        registerCls=registerCls, **kwargs)

class RookStatusLeds(I2cComponent):
   def __init__(self, addr=None, leds=None, **kwargs):
      drivers = [
         RookStatusLedKernelDriver(addr=addr),
         RookLedSysfsDriver(sysfsPath='/sys/class/leds/'),
      ]
      super(RookStatusLeds, self).__init__(addr=addr, drivers=drivers, **kwargs)
      for led in leds or []:
         self.createLed(led)

   def createLed(self, led):
      led = LedImpl(name=led.name, colors=led.colors,
                    driver=self.drivers['RookLedSysfsDriver'])
      self.inventory.addLed(led)
      return led

class RookFanCpld(I2cComponent):
   def __init__(self, addr=None, variant=None, **kwargs):
      self.fanCount = {'la': 4, 'tehama': 5}[variant]
      drivers = [RookFanCpldKernelDriver(name='%s_cpld' % variant, addr=addr)]
      self.driver = drivers[0]
      super(RookFanCpld, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def getFanCount(self):
      return self.fanCount

   def addFan(self, desc):
      return self.inventory.addFan(self.driver.getFan(desc))

   def addFanLed(self, desc):
      return self.inventory.addLed(self.driver.getFanLed(desc))
