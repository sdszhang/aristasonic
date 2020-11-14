import os

from .i2c import I2cKernelDriver
from .sysfs import FanSysfsImpl, LedSysfsDriver, LedSysfsImpl

class RookLedSysfsDriver(LedSysfsDriver):
   def getLedColor(self, led):
      onColors = []
      for color in led.colors:
         ledName = "rook_leds:%s:%s" % (color, led.name)
         path = os.path.join(self.sysfsPath, ledName, 'brightness')
         if self.read(ledName, path=path) == '1':
            onColors.append(color)
      return ', '.join(onColors) or 'off'

   def setLedColor(self, led, value):
      if value not in led.colors:
         return # raise ValueError ?
      for color in led.colors:
         ledName = "rook_leds:%s:%s" % (color, led.name)
         path = os.path.join(self.sysfsPath, ledName, 'brightness')
         self.write(ledName, '1' if value == color else '0', path=path)

class RookStatusLedKernelDriver(I2cKernelDriver):
   def __init__(self, name='rook_leds', module='rook-led-driver', **kwargs):
      super(RookStatusLedKernelDriver, self).__init__(name=name, module=module,
                                                      **kwargs)

class RookFanCpldKernelDriver(I2cKernelDriver):
   def __init__(self, name=None, module='rook-fan-cpld', **kwargs):
      super(RookFanCpldKernelDriver, self).__init__(name=name, module=module,
                                                    **kwargs)

   def getFan(self, desc):
      return FanSysfsImpl(self, desc)

   def getFanLed(self, desc):
      return LedSysfsImpl(self, desc)
