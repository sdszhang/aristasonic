
from . import InventoryInterface

class Fan(InventoryInterface):
   def getId(self):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def getModel(self):
      raise NotImplementedError()

   def getSpeed(self):
      raise NotImplementedError()

   def setSpeed(self, speed):
      raise NotImplementedError()

   def getDirection(self):
      raise NotImplementedError()

   def getFault(self):
      raise NotImplementedError()

   def getStatus(self):
      raise NotImplementedError()

   def getPosition(self):
      raise NotImplementedError()

   def getLed(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "speed": self.getSpeed() if ctx.performIo else None,
         "direction": self.getDirection() if ctx.performIo else None,
      }

class FanSlot(InventoryInterface):
   def getId(self):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def getModel(self):
      raise NotImplementedError()

   def getPresence(self):
      raise NotImplementedError()

   def getFans(self):
      raise NotImplementedError()

   def getDirection(self):
      raise NotImplementedError()

   def getLed(self):
      raise NotImplementedError()

   def getFault(self):
      raise NotImplementedError()

   def getMaxPowerDraw(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "presence": self.getPresence() if ctx.performIo else None,
         "fans": [ f.genDiag(ctx) for f in self.getFans() ],
      }
