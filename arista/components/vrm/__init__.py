
from ...core.component.i2c import I2cComponent
from ...core.log import getLogger

from ...drivers.vrm import VrmI2cUserDriver

logging = getLogger(__name__)

class Vrm(I2cComponent):
   DRIVER = VrmI2cUserDriver

   def __init__(self, vouts=None, identify=None, **kwargs):
      super().__init__(**kwargs)
      self.vouts = vouts
      if identify:
         self.driver.IDENTIFY_SEQUENCE = identify

   def identify(self):
      return self.driver.identify()

   def voutCommand(self, vout):
      logging.debug('Configuring %s VOUT to 0x%04x', self, vout)
      # TODO: use RegisterMap when variable size registers are supported
      VOUT_COMMAND_REG = 0x21
      self.driver.write_word_data(VOUT_COMMAND_REG, vout)

   def setVoutValue(self, value):
      self.voutCommand(self.vouts[value])

class VrmNotFoundError(Exception):
   pass

class VrmDetector(object):
   def __init__(self, vrms):
      self.vrms = vrms
      self.vrm_ = None

   def __str__(self):
      return self.__class__.__name__

   def identifyVrm(self):
      for vrm in self.vrms:
         if vrm.identify():
            logging.debug('%s: found VRM %s', self, vrm)
            return vrm
      raise VrmNotFoundError

   @property
   def vrm(self):
      if self.vrm_ is None:
         self.vrm_ = self.identifyVrm()
      return self.vrm_
