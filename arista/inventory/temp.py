
from . import InventoryInterface

class Temp(InventoryInterface):
   def getName(self):
      raise NotImplementedError

   def getDesc(self):
      raise NotImplementedError

   def getPresence(self):
      raise NotImplementedError

   def getModel(self):
      raise NotImplementedError

   def getStatus(self):
      raise NotImplementedError

   def getTemperature(self):
      raise NotImplementedError

   def getLowThreshold(self):
      raise NotImplementedError

   def getLowCriticalThreshold(self):
      raise NotImplementedError

   def getHighThreshold(self):
      raise NotImplementedError

   def getHighCriticalThreshold(self):
      raise NotImplementedError

   def setLowThreshold(self, value):
      raise NotImplementedError

   def setHighThreshold(self, value):
      raise NotImplementedError

   def __diag__(self, ctx):
      return {
         "value": self.getTemperature() if ctx.performIo else None,
         "desc": self.getDesc().__diag__(ctx),
         "low_thresh": self.getLowThreshold(),
         "high_thresh": self.getHighThreshold(),
      }
