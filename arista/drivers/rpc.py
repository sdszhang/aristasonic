
from ..core.driver.user import UserDriver
from ..descs.led import LedColor
from ..inventory.led import Led

class RpcLedImpl(Led):
   def __init__(self, driver, desc, **kwargs):
      self.driver = driver
      self.desc = desc

   def getName(self):
      return self.desc.name

   def getColor(self):
      # TODO: do RPC code here
      return LedColor.OFF

   def setColor(self, color):
      # TODO: do RPC code here
      return True

   def isStatusLed(self):
      return True

class LinecardRpcClientDriver(UserDriver):
   def __init__(self, **kwargs):
      super().__init__(**kwargs)
      # TODO init RPC client
      self.client = None

   def getLed(self, desc, **kwargs):
      return RpcLedImpl(self, desc)

