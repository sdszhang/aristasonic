
from ...core.register import Register, RegBitField

from ..cpld import SysCpld, SysCpldCommonRegistersV2

class LorikeetCpldRegisters(SysCpldCommonRegistersV2):
   pass

class LorikeetSysCpld(SysCpld):
   REGISTER_CLS = LorikeetCpldRegisters
