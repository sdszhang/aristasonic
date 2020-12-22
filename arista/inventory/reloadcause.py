
from . import InventoryInterface, diagcls, diagmethod

@diagcls
class ReloadCause(InventoryInterface):
   @diagmethod('time')
   def getTime(self):
      raise NotImplementedError

   @diagmethod('cause')
   def getCause(self):
      raise NotImplementedError
