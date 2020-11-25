from ..descs.led import LedColor
from ..inventory.led import Led

class LedImpl(Led):
   def __init__(self, name=None, driver=None, **kwargs):
      self.name = name
      self.driver = driver
      self.__dict__.update(kwargs)

   def getColor(self):
      return self.driver.getLedColor(self)

   def setColor(self, color):
      return self.driver.setLedColor(self, color)

   def getName(self):
      return self.name

   def isStatusLed(self):
      return not 'sfp' in self.name

class LedGpioImpl(Led):
   def __init__(self, name, gpio, colorActive=LedColor.RED,
                colorInactive=LedColor.OFF, **kwargs):
      self.name = name
      self.gpio = gpio
      self.colorActive = colorActive
      self.colorInactive = colorInactive
      self.__dict__.update(kwargs)

   def getName(self):
      return self.name

   def getColor(self):
      if self.gpio.isActive():
         return self.colorActive
      return self.colorInactive

   def setColor(self, color):
      if color == self.colorActive:
         self.gpio.setActive(True)
      else:
         self.gpio.setActive(False)
      return True

   def isStatusLed(self):
      return True
