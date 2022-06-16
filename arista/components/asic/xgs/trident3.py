
from ....core.quirk import Quirk
from ....core.register import RegisterMap, Register, RegBitRange

from ....libs.wait import waitFor

from . import XgsSwitchChip

class Trident3(XgsSwitchChip):
   pass

class Trident3X2RegMap(RegisterMap):
   DMU_PCU_OTP_CONFIG_9 = Register(0x6c,
      RegBitRange(21, 24, name='avsValue'),
      name='configReg',
   )

class Trident3X2(Trident3):
   REGISTER_CLS = Trident3X2RegMap

   class AvsQuirk(Quirk):

      DELAYED = True

      def __init__(self, avs):
         self.avs = avs

      def waitAsicRegisterReady(self, asic):
         waitFor(
            lambda: asic.driver.regs.configReg() != 0xffffffff,
            description='Asic config register ready',
         )

      def run(self, component):
         self.waitAsicRegisterReady(component)
         value = component.driver.regs.avsValue()
         vout = {
            0x1: 0x018d, # 0.800V
            0x2: 0x019a, # 0.825V
            0x4: 0x01a7, # 0.850V
         }.get(value)
         if vout is not None:
             self.avs.voutCommand(vout)
