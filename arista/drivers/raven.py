
from ..core.driver import KernelDriver

from .sysfs import FanSysfsImpl, LedSysfsImpl

class RavenFanKernelDriver(KernelDriver):
   def __init__(self, module='raven-fan-driver', **kwargs):
      super(RavenFanKernelDriver, self).__init__(module=module, **kwargs)

   def getSysfsPath(self):
      return '/sys/devices/platform/sb800-fans'

   def getFan(self, desc):
      return FanSysfsImpl(self, desc)

   def getFanLed(self, desc):
      return LedSysfsImpl(self, desc)
