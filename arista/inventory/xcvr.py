
from . import InventoryInterface, diagcls, diagmethod

@diagcls
class Xcvr(InventoryInterface):

   SFP = 0
   QSFP = 1
   OSFP = 2

   ADDR = 0x50

   @classmethod
   def typeStr(cls, typeIndex):
      return ['sfp', 'qsfp', 'osfp'][typeIndex]

   @diagmethod('type')
   def getType(self):
      raise NotImplementedError

   @diagmethod('name')
   def getName(self):
      raise NotImplementedError

   @diagmethod('present', io=True)
   def getPresence(self):
      raise NotImplementedError

   @diagmethod('lpmode', io=True)
   def getLowPowerMode(self):
      raise NotImplementedError

   def setLowPowerMode(self, value):
      raise NotImplementedError

   @diagmethod('intr', diag=True)
   def getInterruptLine(self):
      raise NotImplementedError

   @diagmethod('reset', diag=True)
   def getReset(self):
      raise NotImplementedError
