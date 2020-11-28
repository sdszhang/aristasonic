
from ..inventory.fan import FanSlot

class FanSlotImpl(FanSlot):
   def __init__(self, slot):
      self.slot = slot

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getModel(self):
      return self.slot.getModel()

   def getPresence(self):
      return self.slot.getPresence()

   def getFans(self):
      return self.slot.getFans()

   def getDirection(self):
      return self.slot.getFans()[0].getDirection()

   def getLed(self):
      return self.slot.getLed()

   def getMaxPowerDraw(self):
      return self.slot.getMaxPowerDraw()

   def getFault(self):
      return self.slot.getFault()
