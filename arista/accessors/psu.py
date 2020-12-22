from ..inventory.psu import Psu

class PsuImpl(Psu):
   def __init__(self, psuId=1, driver=None, led=None, **kwargs):
      self.psuId = psuId
      self.driver = driver
      self.led = led
      self.__dict__.update(kwargs)

   def getId(self):
      return self.psuId

   def getName(self):
      return 'psu%s' % self.psuId

   def getModel(self):
      return "N/A"

   def getSerial(self):
      return "N/A"

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)

   def getLed(self):
      return self.led

class MixedPsuImpl(Psu):
   def __init__(self, psuId=1, presenceDriver=None, statusDriver=None, led=None,
                **kwargs):
      self.psuId = psuId
      self.presenceDriver = presenceDriver
      self.statusDriver = statusDriver
      self.led = led
      self.__dict__.update(kwargs)

   def getId(self):
      return self.psuId

   def getName(self):
      return 'psu%s' % self.psuId

   def getModel(self):
      return "N/A"

   def getSerial(self):
      return "N/A"

   def getPresence(self):
      return self.presenceDriver.getPsuPresence(self)

   def getStatus(self):
      return self.statusDriver.getPsuStatus(self)

   def getLed(self):
      return self.led

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
