
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

      TPS549D22 = {
         0x1: 0x019a, # 0.800V
         0x2: 0x01a6, # 0.825V
         0x4: 0x01b3, # 0.850V
         0x8: 0x01c0, # 0.875V
      }

      def __init__(self, avs, mapping):
         self.avs = avs
         self.mapping = mapping

      def waitAsicRegisterReady(self, asic):
         waitFor(
            lambda: asic.driver.regs.configReg() != 0xffffffff,
            description='Asic config register ready',
         )

      def run(self, component):
         self.waitAsicRegisterReady(component)
         value = component.driver.regs.avsValue()
         vout = self.mapping.get(value)
         if vout is not None:
            self.avs.voutCommand(vout)
