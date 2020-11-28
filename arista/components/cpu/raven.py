from ...core.component import Component
from ...core.log import getLogger

from ...drivers.raven import RavenFanKernelDriver

logging = getLogger(__name__)

class RavenFanComplex(Component):
   def __init__(self, addr=None, **kwargs):
      drivers = [RavenFanKernelDriver(addr=addr)]
      self.driver = drivers[0]
      super(RavenFanComplex, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def addFan(self, desc):
      return self.inventory.addFan(self.driver.getFan(desc))

   def addFanLed(self, desc):
      return self.inventory.addLed(self.driver.getFanLed(desc))
