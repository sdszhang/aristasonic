
from . import InventoryInterface, diagcls, diagmethod

@diagcls
class Psu(InventoryInterface):
   @diagmethod('name')
   def getName(self):
      raise NotImplementedError

   @diagmethod('model')
   def getModel(self):
      raise NotImplementedError

   @diagmethod('serial')
   def getSerial(self):
      raise NotImplementedError

   @diagmethod('present', io=True)
   def getPresence(self):
      raise NotImplementedError

   @diagmethod('status', io=True)
   def getStatus(self):
      raise NotImplementedError
