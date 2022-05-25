
from ..core.config import Config
from ..core.driver.user import UserDriver
from ..descs.led import LedColor
from ..inventory.led import Led
from ..utils.rpc.client import RpcClient

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
   def __init__(self, slotId=None, **kwargs):
      super().__init__(**kwargs)
      self.client = RpcClient(Config().api_rpc_sup, Config().api_rpc_port)

   def getLed(self, desc, **kwargs):
      return RpcLedImpl(self, desc, **kwargs)

