
from .i2c import I2cKernelDriver
from .sysfs import FanSysfsImpl

class Max31790KernelDriver(I2cKernelDriver):
   def __init__(self, name=None, module='amax31790', **kwargs):
      super(Max31790KernelDriver, self).__init__(name=name, module=module, **kwargs)

   def getFan(self, desc):
      return FanSysfsImpl(self, desc=desc)
