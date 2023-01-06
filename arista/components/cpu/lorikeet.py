
from ...core.register import RegisterMap, Register, RegBitField, RegBitRange

from ..cpld import SysCpld, SysCpldCommonRegistersV2

class LorikeetCpldRegisters(SysCpldCommonRegistersV2):
   pass

class LorikeetSysCpld(SysCpld):
   REGISTER_CLS = LorikeetCpldRegisters

class LorikeetPrimeScdReloadCauseRegisters(RegisterMap):
   LATCHED_CAUSE = Register(0x4F80,
      RegBitRange(0, 7, name='latchedCause'),
   )
   LATCHED_CAUSE_RTC0 = Register(0x4F84,
      RegBitRange(0, 15, name='latchedFractional'),
   )
   LATCHED_CAUSE_RTC1 = Register(0x4F88, name='latchedSeconds')
   LAST_CAUSE = Register(0x4F8C,
      RegBitRange(0, 7, name='lastCause'),
   )
   LAST_CAUSE_RTC0 = Register(0x4F90,
      RegBitRange(0, 15, name='lastFractional'),
   )
   LAST_CAUSE_RTC1 = Register(0x4F94, name='lastSeconds')
   RTC0 = Register(0x4FA8,
      RegBitRange(0, 15, name='rtcFractional', ro=False),
   )
   RTC1 = Register(0x4FAC, name='rtcSeconds', ro=False)
   CAUSE_CTRL = Register(0x4F98,
      RegBitField(0, name='clearFault', ro=False),
      RegBitRange(16, 31, name='faultTest', ro=False),
   )
