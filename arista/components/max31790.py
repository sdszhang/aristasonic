
from ..drivers.max31790 import Max31790KernelDriver

from .common import I2cComponent

class Max31790(I2cComponent):
   def __init__(self, addr, variant, fans=None, **kwargs):
      name = 'amax31790_%s' % variant
      drivers = [Max31790KernelDriver(addr=addr, name=name)]
      super(Max31790, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.driver = self.drivers['Max31790KernelDriver']
      for fan in fans or []:
         self.addFan(fan)

   def addFan(self, desc, **kwargs):
      return self.inventory.addFan(self.driver.getFan(desc, **kwargs))
