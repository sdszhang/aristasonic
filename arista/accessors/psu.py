from ..inventory.psu import Psu

class PsuSlotImpl(Psu):
   def __init__(self, slot=None, sensors=None, fans=None, **kwargs):
      self.slot = slot
      self.psuId = slot.slotId
      self.sensors = sensors
      self.fans = fans
      self.__dict__.update(kwargs)

   def getId(self):
      return self.slot.slotId

   def getName(self):
      return 'psu%s' % self.slot.slotId

   def getModel(self):
      if not self.getPresence():
         return "N/A"
      return self.slot.model.identifier.aristaName

   def getSerial(self):
      if not self.getPresence():
         return "N/A"
      return self.slot.model.identifier.metadata['serial']

   def getPresence(self):
      return self.slot.getPresence()

   def getStatus(self):
      return self.slot.isPowerGood()

   def getLed(self):
      return self.slot.led
