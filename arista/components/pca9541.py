
from .common import I2cComponent
from ..core.types import I2cAddr
from ..drivers.pca9541 import Pca9541I2cDevDriver

class PcaI2cAddr(I2cAddr):
   def __init__(self, pca, addr):
      super(PcaI2cAddr, self).__init__(None, addr)
      self.pca_ = pca

   @property
   def bus(self):
      return self.pca_.addr.bus

class Pca9541(I2cComponent):
   def __init__(self, addr, drivers=None, **kwargs):
      drivers = drivers or [Pca9541I2cDevDriver(addr=addr)]
      super(Pca9541, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def takeOwnership(self):
      return self.drivers['Pca9541I2cDevDriver'].takeOwnership()

   def ping(self):
      return self.drivers['Pca9541I2cDevDriver'].ping()

   def i2cAddr(self, addr):
      return PcaI2cAddr(self, addr)
