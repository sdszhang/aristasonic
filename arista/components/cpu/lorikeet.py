
from ...core.register import Register, RegBitField

from ..cpld import SysCpld, SysCpldCommonRegisters

class LorikeetCpldRegisters(SysCpldCommonRegisters):
   MINOR = Register(0x00, name='revisionMinor')
   PWR_CTRL_STS = Register(0x05,
      RegBitField(7, 'dpPower', ro=False),
      RegBitField(0, 'switchCardPowerGood'),
   )
   INT_STS = Register(0x08,
      RegBitField(4, 'dpPowerFail'),
      RegBitField(3, 'overtemp'),
      RegBitField(0, 'scdCrcError'),
   )
   SCD_CTRL_STS = Register(0x0A,
      RegBitField(5, 'scdReset', ro=False),
      RegBitField(1, 'scdInitDone'),
      RegBitField(0, 'scdConfDone'),
   )
   PWR_CYC_EN = Register(0x17,
      RegBitField(0, 'powerCycleOnCrc', ro=False),
   )

class LorikeetSysCpld(SysCpld):
   REGISTER_CLS = LorikeetCpldRegisters
