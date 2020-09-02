
from .component import Priority
from .exception import UnknownPlatformError
from .inventory import Inventory, Slot
from .log import getLogger
from .platform import getPlatformCls
from .sku import Sku

logging = getLogger(__name__)

# Starting slot id for linecard and fabric cards
LC_BASE_SLOTID = 3
FC_BASE_SLOTID = 51

class Card(Sku):

   CPU_CLS = None

   def __init__(self, slot=None, standbyOnly=False, noStandby=False, **kwargs):
      self.slot = slot
      self.standby = None
      self.main = None
      self.cpu = None
      super(Card, self).__init__(inventory=Inventory(), **kwargs)
      if slot:
         if not noStandby:
            self.loadStandbyDomain()
         if not standbyOnly:
            self.loadMainDomain()
      else:
         self.loadCpuDomain()

   def loadStandbyDomain(self):
      raise NotImplementedError

   def loadMainDomain(self):
      raise NotImplementedError

   def loadCpuDomain(self):
      raise NotImplementedError

   def powerOnIs(self, on, lcpuCtx=None):
      raise NotImplementedError

   def poweredOn(self):
      raise NotImplementedError

   def hasCpuModule(self):
      return self.CPU_CLS is not None

   def setup(self, filters=Priority.defaultFilter):
      super(Card, self).setup()
      super(Card, self).finish(filters=filters)

   def setupStandby(self, filters=Priority.defaultFilter):
      self.standby.setup()
      self.standby.finish(filters)

   def setupMain(self, filters=Priority.defaultFilter):
      self.main.setup()
      self.main.finish(filters)

   def __str__(self):
      if self.slot.parent is self:
         return '%s()' % self.__class__.__name__
      else:
         return '%s(slotId=%d)' % (self.__class__.__name__, self.slot.slotId)

class CardSlot(Slot):
   def __init__(self, parent, slotId):
      self.slotId = slotId
      self.parent = parent
      self.card = None

   def getEeprom(self):
      raise NotImplementedError

   def disablePciPort(self):
      self.parent.pciSwitch.disable(self.slotId)

   def enablePciPort(self):
      self.parent.pciSwitch.enable(self.slotId)

   def loadCard(self, card=None, **kwargs):
      if card is None:
         assert self.card, "No default card definition loaded"
         if not self.getPresence():
            logging.debug('Card slot %d is not present', self.slotId)
            return

         eeprom = self.getEeprom()
         sku = eeprom.get('SKU')
         try:
            cls = getPlatformCls(sku)
            # add some Config() for noStandby
            logging.info('Loading card %s in slot %d', cls.__name__, self.slotId)
            card = cls(self, **kwargs)
         except UnknownPlatformError:
            logging.warning('Unsupported card %s for slot %d', sku, self.slotId)
            return

      self.card = card
      self.card.refresh()
