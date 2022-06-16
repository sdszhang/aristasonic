
from ...core.component.i2c import I2cComponent
from ...core.log import getLogger

from ...drivers.vrm import VrmI2cUserDriver

logging = getLogger(__name__)

class Vrm(I2cComponent):
   DRIVER = VrmI2cUserDriver

   def voutCommand(self, vout):
      logging.debug('Configuring %s VOUT to 0x%04x', self, vout)
      # TODO: use RegisterMap when variable size registers are supported
      VOUT_COMMAND_REG = 0x21
      self.driver.write_word_data(VOUT_COMMAND_REG, vout)
