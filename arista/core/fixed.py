from .component import Priority
from .config import Config
from .inventory import Inventory
from .metainventory import MetaInventory
from .platform import getSysEepromData
from .sku import Sku

class FixedSystem(Sku):

   CHASSIS = None

   def __init__(self, inventory=None, **kwargs):
      inventory = inventory or Inventory()
      super(FixedSystem, self).__init__(inventory=inventory, **kwargs)

   def getEeprom(self):
      return getSysEepromData()

   def getInventory(self):
      if Config().use_metainventory:
         return MetaInventory(self.iterInventory())
      return self.inventory

   def setup(self, filters=Priority.defaultFilter):
      super(FixedSystem, self).setup()
      super(FixedSystem, self).finish(filters)

   def __str__(self):
      return '%s()' % self.__class__.__name__

class FixedChassis(object):
   FAN_SLOTS = None
   FAN_COUNT = None
   PSU_SLOTS = None
   HEIGHT_RU = None
