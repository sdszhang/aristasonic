
from . import InventoryInterface

class Interrupt(InventoryInterface):
   def set(self):
      raise NotImplementedError()

   def clear(self):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def getFile(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         # TODO: get ?
         "name": self.getName(),
         "file": self.getFile(),
      }
