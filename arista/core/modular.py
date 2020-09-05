from .config import Config
from .log import getLogger
from .metainventory import MetaInventory
from .sku import Sku

logging = getLogger(__name__)

class Modular(Sku):

   CARD_SLOT_CLS = None
   CARD_CLS = None

   NUM_SUPERVISORS = 2
   NUM_LINECARDS = 8
   NUM_FABRICS = 6
   NUM_FANS = 48
   NUM_PSUS = 20

   def __init__(self, inventory=None, **kwargs):
      inventory = inventory or MetaInventory()
      super(Modular, self).__init__(inventory=inventory, **kwargs)
      self.inventory.invs = iter(self.iterAllInventories())

      self.supervisors = [None] * self.NUM_SUPERVISORS
      self.active = None

   def genDiag(self, ctx):
      if ctx.performIo:
         self.loadLinecards()
         self.loadFabrics()

      return {
         "version": 1,
         "name": self.__class__.__name__,
         "supervisors": [s.genDiag(ctx) for s in self.iterSupervisors()],
         "linecardSlots": [s.genDiag(ctx) for s in self.iterLinecards()],
         "fabricSlots": [s.genDiag(ctx) for s in self.iterFabrics()],
         "fanSlots": [s.genDiag(ctx) for s in self.iterFans()],
         "psuSlots": [s.genDiag(ctx) for s in self.iterPsus()],
      }

   def iterCards(self):
      for linecard in self.iterLinecards():
         yield linecard
      for fabric in self.iterFabrics():
         yield fabric

   def iterAllInventories(self):
      for inv in self.active.iterInventory():
         yield inv
      for card in self.iterCards():
         yield card.inventory

   def getEeprom(self):
      assert self.active
      return self.active.readChassisEeprom()

   def insertSupervisor(self, supervisor, slotId, active=False):
      assert self.supervisors[slotId] is None
      self.supervisors[slotId] = supervisor
      if active:
         self.active = supervisor

   def iterSupervisors(self, presentOnly=True):
      for sup in self.supervisors:
         if sup is None and presentOnly:
            continue
         yield sup

   def loadLinecards(self, slotIds=None):
      for slot in self.active.linecardSlots[:self.NUM_LINECARDS]:
         if slotIds is not None and slot.slotId not in slotIds:
            continue
         logging.debug('Loading linecard slot %d', slot.slotId)
         standbyOnly = Config().linecard_standby_only
         slot.loadCard(standbyOnly=standbyOnly)

   def loadFabrics(self, slotIds=None):
      for slot in self.active.fabricSlots[:self.NUM_FABRICS]:
         if slotIds is not None and slot.slotId not in slotIds:
            continue
         logging.debug('Loading fabric slot %d', slot.slotId)
         slot.loadCard()

   def loadPsus(self, slotIds=None):
      for slot in self.active.psuSlots[:self.NUM_PSUS]:
         if slotIds is not None and slot.slotId not in slotIds:
            continue
         logging.debug('Loading psu slot %d', slot.slotId)
         slot.loadPsu()

   def _iterSlots(self, slots, count, presentOnly=True):
      for slot in slots[:count]:
         if slot.card is None and presentOnly:
            continue
         yield slot.card

   def iterLinecards(self, presentOnly=True):
      return self._iterSlots(self.active.linecardSlots, self.NUM_LINECARDS,
                             presentOnly=presentOnly)

   def iterFabrics(self, presentOnly=True):
      return self._iterSlots(self.active.fabricSlots, self.NUM_FABRICS,
                             presentOnly=presentOnly)

   def iterFans(self, presentOnly=True):
      return self._iterSlots(self.active.fanSlots, self.NUM_FANS,
                             presentOnly=presentOnly)

   def iterPsus(self, presentOnly=True):
      return self._iterSlots(self.active.psuSlots, self.NUM_PSUS,
                             presentOnly=presentOnly)
