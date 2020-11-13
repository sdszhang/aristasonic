
from .i2c import I2cKernelDriver
from .sysfs import FanSysfsImpl, LedSysfsImpl

class CrowFanCpldKernelDriver(I2cKernelDriver):
   def __init__(self, name='crow_cpld', module='crow-fan-driver', **kwargs):
      super(CrowFanCpldKernelDriver, self).__init__(name=name, module=module,
                                                    **kwargs)

   def getFan(self, desc):
      return FanSysfsImpl(self, desc)

   def getFanLed(self, desc):
      return LedSysfsImpl(self, desc)
