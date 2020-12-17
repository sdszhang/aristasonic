
import copy

from .component import SlotComponent, Priority
from .log import getLogger
from .utils import JsonStoredData, inSimulation

from ..accessors.psu import PsuSlotImpl
from ..drivers.pmbus import PsuPmbusDetect
from ..descs.psu import PsuDesc

logging = getLogger(__name__)

class PsuIdent(object):
   def __init__(self, partName=None, aristaName=None, airflow=None, metadata=None):
      self.partName = partName
      self.aristaName = aristaName
      self.airflow = airflow
      self.metadata = metadata

class PsuSlot(SlotComponent):
   def __init__(self, slotId=None, desc=None, addrFunc=None, psus=None,
                presentGpio=None, inputOkGpio=None, outputOkGpio=None, led=None,
                **kwargs):
      super(PsuSlot, self).__init__(priority=Priority.POWER, **kwargs)
      self.slotId = slotId
      self.model = None

      self.desc = desc
      self.addrFunc = addrFunc
      self.presentGpio = presentGpio
      self.inputOkGpio = inputOkGpio
      self.outputOkGpio = outputOkGpio
      self.led = led
      self.psus = psus

      self.addrFunc(0x00) # workaround to configure a bus wide parameter
      self.psuInv = self.inventory.addPsu(PsuSlotImpl(self))
      self.load(cacheOnly=True) # no IO in the constructor

   def autodetectPsuModel(self):
      psus = []
      for psuCls in self.psus:
         psu = psuCls.tryLoadPsu(self)
         if psu is not None:
            psus.append(psu)

      if not psus:
         return None
      assert len(psus) == 1, 'Multiple PSUs matched the description'
      return psus[0]

   def getCacheStore(self):
      return JsonStoredData('psu_slot_%d.json' % self.slotId)

   def getCache(self):
      cache = self.getCacheStore()
      return cache.readOrClear()

   def setCache(self):
      cache = self.getCacheStore()
      cache.write({
         'cls': self.model.__class__.__name__,
         'identifier': self.model.identifier.__dict__,
      }, mode='w+')

   def loadModelFromCache(self):
      data = self.getCache()
      if data is None:
         return None

      clsname = data['cls']
      identifier = PsuIdent(**data['identifier'])
      for psuCls in self.psus:
         if psuCls.__name__ == clsname:
            return psuCls(identifier)

      return None

   def logPsuInformation(self):
      logging.debug("PSU %d name: %s", self.slotId, self.model.identifier.aristaName)
      for key, value in self.model.identifier.metadata.items():
         logging.debug("PSU %d %s: %s", self.slotId, key, value)

   def loadPsuModel(self, cacheOnly=False):
      self.model = self.loadModelFromCache()
      if self.model is not None:
         logging.debug("PSU %d loaded from cache", self.slotId)
         return self.model

      if cacheOnly:
         logging.debug("PSU %d model not found in cache, skipping IO", self.slotId)
         return None

      self.model = self.autodetectPsuModel()
      if self.model is None:
         logging.error("PSU %d unknown, discovery failed", self.slotId)
         return None

      logging.debug("PSU %d discovered", self.slotId)
      self.logPsuInformation()

      if not inSimulation():
         self.setCache()

      return self.model

   def addPsu(self, desc):
      psu = self.newComponent(
         self.model.PMBUS_CLS,
         name=self.model.DRIVER,
         addr=self.addrFunc(self.model.PMBUS_ADDR),
      )
      psu.addTempSensors(desc.sensors)
      psu.addFans(desc.fans)

   def load(self, cacheOnly=False):
      if not cacheOnly and not self.getPresence():
         logging.debug("PSU %d is not inserted", self.slotId)
         return

      if not self.loadPsuModel(cacheOnly=cacheOnly):
         return

      desc = copy.deepcopy(self.model.DESCRIPTION)
      desc.setPsuId(self.slotId)
      self.addPsu(desc)

   def getPresence(self):
      return self.presentGpio.isActive()

   def _getGpioActiveOr(self, gpio):
      if gpio is None:
         return True
      if isinstance(gpio, list):
         return bool((g for g in gpio if g.isActive()))
      return gpio.isActive()

   def isInputGood(self):
      return self._getGpioActiveOr(self.inputOkGpio)

   def isOutputGood(self):
      return self._getGpioActiveOr(self.outputOkGpio)

   def isPowerGood(self):
      if not self.getPresence():
         return False
      if not self.isInputGood():
         return False
      return self.isOutputGood()

   def setup(self):
      self.load()
      if self.components:
         # initialize the PSU, iterComponent will not run on it since the list
         # has already been computed.
         self.components[0].setup()
         self.components[0].finish()

class PsuModel(object):
   MANUFACTURER = None
   IDENTIFIERS = []
   IPMI_ADDR = 0x50
   PMBUS_ADDR = None

   PMBUS_CLS = None
   DRIVER = 'pmbus'
   DESCRIPTION = PsuDesc()

   AUTODETECT_IPMI = True
   AUTODETECT_PMBUS = True

   def __init__(self, identifier):
      self.identifier = identifier

   def getManufacturer(self):
      return self.MANUFACTURER

   def getProductName(self):
      return self.identifier.aristaName

   @classmethod
   def detectIpmi(cls, addr):
      # TODO: Add ipmi detection
      return None

   @classmethod
   def detectPmbus(cls, addr):
      detector = PsuPmbusDetect(addr)
      try:
         logging.debug('testing model %s for %s : "%s"', cls.__name__,
                       detector.id(), detector.model())
         if cls.MANUFACTURER.lower() != detector.id().lower():
            return None
         for ident in cls.IDENTIFIERS:
            if ident.partName.rstrip() == detector.model().rstrip():
               ident = copy.deepcopy(ident)
               ident.metadata = detector.getMetadata()
               return ident
      except Exception: # pylint: disable=broad-except
         logging.error("something happened while trying to detect the psu")
      return None

   @classmethod
   def detectPsu(cls, addrFunc):
      identifier = None
      if cls.AUTODETECT_PMBUS and cls.PMBUS_ADDR:
         identifier = cls.detectPmbus(addrFunc(cls.PMBUS_ADDR))
      if cls.AUTODETECT_IPMI and cls.IPMI_ADDR and identifier is None:
         identifier = cls.detectIpmi(addrFunc(cls.IPMI_ADDR))
      return identifier

   @classmethod
   def tryLoadPsu(cls, slot, *args, **kwargs):
      identifier = cls.detectPsu(slot.addrFunc)
      if identifier is None:
         return None
      return cls(identifier, *args, **kwargs)
