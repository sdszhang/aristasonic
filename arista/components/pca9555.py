from __future__ import absolute_import, division, print_function

from ..accessors.led import LedGpioImpl

from ..drivers.pca9555 import Pca9555I2cDevDriver

from .common import I2cComponent

class Pca9555(I2cComponent):
   def __init__(self, addr, registerCls=None, **kwargs):
      drivers = [Pca9555I2cDevDriver(addr=addr, registerCls=registerCls)]
      super(Pca9555, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.driver = drivers[0]

   def resetConfig(self):
      self.drivers['Pca9555I2cDevDriver'].reset()

   def addGpio(self, name):
      return self.inventory.addGpio(self.driver.getGpio(name))

   def addGpioLed(self, name, **kwargs):
      return self.inventory.addLed(LedGpioImpl(name, self.addGpio(name), **kwargs))

   def __getattr__(self, key):
      driver = self.drivers['Pca9555I2cDevDriver']
      return getattr(driver.regs, key)
