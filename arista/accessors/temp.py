
from ..inventory.temp import Temp

class TempImpl(Temp):
   def __init__(self, sensor, driver=None, **kwargs):
      self.sensor = sensor
      self.name = sensor.name
      self.driver = driver
      self.__dict__.update(kwargs)

   def getName(self):
      return self.name

   def getDesc(self):
      return self.sensor

   def getPresence(self):
      return self.driver.getPresence(self.sensor)

   def getModel(self):
      return "N/A"

   def getStatus(self):
      return True

   def getTemperature(self):
      return self.driver.getTemperature(self.sensor)

   def getLowThreshold(self):
      return self.driver.getLowThreshold(self.sensor)

   def setLowThreshold(self, value):
      return self.driver.setLowThreshold(self.sensor, value)

   def getHighThreshold(self):
      return float(self.sensor.critical)

   def setHighThreshold(self, value):
      self.sensor.critical = value
      return self.driver.setHighThreshold(self.sensor, value)

   def getHighCriticalThreshold(self):
      return self.sensor.critical

   def getLowCriticalThreshold(self):
      return self.getLowThreshold()
