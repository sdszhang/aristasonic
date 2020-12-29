
from ...core.component import Priority
from ...core.component.i2c import I2cComponent
from ...core.register import Register, RegBitField

from ...drivers.rook import (
   LaFanCpldKernelDriver,
   TehamaFanCpldKernelDriver,
   RookStatusLedKernelDriver,
)

from ..cpld import SysCpld, SysCpldCommonRegisters

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
   REGISTER_CLS = RookCpldRegisters

class RookStatusLeds(I2cComponent):
   DRIVER = RookStatusLedKernelDriver
   PRIORITY = Priority.LED

class RookFanCpld(I2cComponent):
   PRIORITY = Priority.COOLING
   FAN_COUNT = 0

class LaFanCpld(RookFanCpld):
   DRIVER = LaFanCpldKernelDriver
   FAN_COUNT = 4

class TehamaFanCpld(RookFanCpld):
   DRIVER = TehamaFanCpldKernelDriver
   FAN_COUNT = 5
