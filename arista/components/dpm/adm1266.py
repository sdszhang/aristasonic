
from ...core.cause import (
   ReloadCauseEntry,
   ReloadCauseProviderHelper,
   ReloadCauseScore,
)
from ...core.component import Priority
from ...core.log import getLogger
from ...core.utils import inSimulation

from ...drivers.dpm.adm1266 import Adm1266UserDriver

from ...libs.date import datetimeToStr
from ...libs.retry import retryGet

from .pmbus import PmbusDpm

logging = getLogger(__name__)

class AdmPriority():
   NONE = 0
   LOW = 10
   NORMAL = 20
   HIGH = 30

class AdmPin():

   GPIO = 'gpio'

   def __init__(self, bit, typ, priority=AdmPriority.NORMAL):
      self.bit = bit
      self.typ = typ
      self.priority = priority

class AdmReloadCauseEntry(ReloadCauseEntry):
   pass

class AdmReloadCauseProvider(ReloadCauseProviderHelper):
   def __init__(self, adm):
      super().__init__(name=str(adm))
      self.adm = adm

   def process(self):
      self.causes = self.adm.getReloadCauses()
      self.extra = {
         # NOTE: device might need some time before grabbing the powerup
         'powerup': retryGet(self.adm.getPowerupCounter, wait=0.2, before=True),
      }

class Adm1266(PmbusDpm):

   DRIVER = Adm1266UserDriver
   PRIORITY = Priority.DPM

   class Registers(PmbusDpm.Registers):
      RUN_TIME_CLOCK = 0xdf

      IC_DEVICE_ID = 0xad
      IC_DEVICE_REV = 0xae

      BLACKBOX_CONFIGURATION = 0xd3
      READ_BLACKBOX = 0xde
      BLACKBOX_INFORMATION = 0xe6

      USER_DATA = 0xe3
      POWERUP_COUNTER = 0xe4

   def __init__(self, addr=None, causes=None, **kwargs):
      super().__init__(addr=addr, **kwargs)
      self.causes = causes
      self.inventory.addReloadCauseProvider(AdmReloadCauseProvider(self))

   def getPowerupCounter(self):
      return self.driver.getPowerupCounter()

   def getVersion(self):
      return self.driver.getVersion()

   def getRunTimeClock(self):
      return self.driver.getRunTimeClock()

   def setRunTimeClock(self):
      self.driver.setRunTimeClock()

   def _getReloadCauses(self):
      causes = []
      for fault in self.driver.getBlackboxFaults():
         logging.debug('fault: %s', fault.summary())
         for name, pin in self.causes.items():
            assert pin.typ == AdmPin.GPIO, \
               "Unhandled cause of type %s" % pin.typ
            if fault.isGpio(pin.bit):
               logging.debug('found: %s', name)
               causes.append(AdmReloadCauseEntry(
                  cause=name,
                  rcTime=datetimeToStr(fault.getTime()),
                  rcDesc='detailed fault powerup=%d' % fault.powerup,
                  score=ReloadCauseScore.LOGGED | ReloadCauseScore.DETAILED |
                        ReloadCauseScore.getPriority(pin.priority),
               ))
      return causes

   def getReloadCauses(self):
      if inSimulation():
         return []

      causes = self._getReloadCauses()
      logging.debug('%s: clearing faults', self)
      self.driver.clearBlackboxFaults()
      return causes
