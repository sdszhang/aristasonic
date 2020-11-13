from ..core.cooling import Airflow
from ..core.log import getLogger
from ..inventory.fan import Fan, FanSlot

logging = getLogger(__name__)

class FanImpl(Fan):
   MIN_FAN_SPEED = 30
   MAX_FAN_SPEED = 100

   def __init__(self, fanId=1, driver=None, led=None, desc=None, **kwargs):
      self.desc = desc
      self.fanId = fanId
      self.driver = driver
      self.led = led
      self.customSpeed = None
      self.__dict__.update(kwargs)

   def getId(self):
      return self.fanId

   def getName(self):
      return 'fan%s' % self.fanId

   def getModel(self):
      return 'N/A'

   def getSpeed(self):
      return self.driver.getFanSpeed(self)

   def getFault(self):
      try:
         return self.driver.getFault(self)
      except Exception: # pylint: disable=broad-except
         return False

   def setSpeed(self, speed):
      if self.customSpeed == self.MAX_FAN_SPEED and speed != self.MAX_FAN_SPEED:
         logging.debug("%s fan speed reduced from max", self.getName())
      elif self.customSpeed != self.MAX_FAN_SPEED and speed == self.MAX_FAN_SPEED:
         logging.warn("%s fan speed set to max", self.getName())
      self.customSpeed = speed
      return self.driver.setFanSpeed(self, speed)

   def getPresence(self):
      return self.driver.getFanPresence(self)

   def getStatus(self):
      return self.driver.getFanStatus(self)

   def getDirection(self):
      try:
         return self.driver.getFanDirection(self)
      except Exception: # pylint: disable=broad-except
         return self.desc.direction if self.desc else Airflow.UNKNOWN

   def getPosition(self):
      return self.desc.position if self.desc else 'N/A'

   def getLed(self):
      return self.led

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
