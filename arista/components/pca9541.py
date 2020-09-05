
from ..core.types import I2cAddr
from ..drivers.pca9541 import Pca9541I2cDevDriver, Pca9541KernelDriver

from .common import I2cComponent

class PcaI2cAddr(I2cAddr):
   def __init__(self, pca, addr):
      super(PcaI2cAddr, self).__init__(None, addr)
      self.pca_ = pca

   @property
   def bus(self):
      return self.pca_.getBus()

class Pca9541(I2cComponent):
   def __init__(self, addr, driverMode='user', **kwargs):
      # TODO: fix driver declaration with DriverSelector
      driverCls = Pca9541I2cDevDriver if driverMode == 'user' else \
                  Pca9541KernelDriver
      drivers = [driverCls(addr=addr)]
      super(Pca9541, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.driver = next(iter(self.drivers.values()))

   def takeOwnership(self):
      return self.driver.takeOwnership()

   def ping(self):
      return self.driver.ping()

   def getBus(self):
      return self.driver.getBus()

   def i2cAddr(self, addr):
      return PcaI2cAddr(self, addr)
