
from .common import I2cComponent
from ..drivers.pca9541 import Pca9541I2cDevDriver

class Pca9541(I2cComponent):
   def __init__(self, addr, drivers=None, **kwargs):
      drivers = drivers or [Pca9541I2cDevDriver(addr=addr)]
      super(Pca9541, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def takeOwnership(self):
      return self.drivers['Pca9541I2cDevDriver'].takeOwnership()

   def ping(self):
      return self.drivers['Pca9541I2cDevDriver'].ping()
