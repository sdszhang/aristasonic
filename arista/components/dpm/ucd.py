from __future__ import with_statement

import datetime

from ...core.cause import (
   ReloadCauseEntry,
   ReloadCauseProviderHelper,
   ReloadCauseScore,
)
from ...core.component import Priority
from ...core.utils import inSimulation
from ...core.log import getLogger

from ...drivers.dpm.ucd import UcdUserDriver

from ...libs.date import datetimeToStr

from .pmbus import PmbusDpm

logging = getLogger(__name__)

class UcdPriority():
   NONE = 0
   LOW = 10
   NORMAL = 20
   HIGH = 30

class UcdGpi():
   def __init__(self, bit, priority=UcdPriority.NORMAL):
      self.bit = bit
      self.priority = priority

class UcdMon():
   def __init__(self, val, priority=UcdPriority.NORMAL):
      self.val = val
      self.priority = priority

class UcdReloadCauseEntry(ReloadCauseEntry):
   pass

class UcdReloadCauseProvider(ReloadCauseProviderHelper):
   def __init__(self, ucd):
      super().__init__(name=str(ucd))
      self.ucd = ucd

   def process(self):
      self.causes = self.ucd.getReloadCauses()

class Ucd(PmbusDpm):

   DRIVER = UcdUserDriver
   PRIORITY = Priority.DPM

   class Registers(PmbusDpm.Registers):
      RUN_TIME_CLOCK = 0xd7

      LOGGED_FAULTS = 0xea
      LOGGED_FAULT_DETAIL_INDEX = 0xeb
      LOGGED_FAULT_DETAIL = 0xec

      LOGGED_FAULTS_COUNT = 13
      LOGGED_FAULT_DETAIL_COUNT = 10

      DEVICE_ID = 0xfd

      def __str__(self):
         return '%s()' % self.__class__.__name__

   gpiSize = 1
   faultValueSize = 2

   faultTimeBase = datetime.datetime(1970, 1, 1)
   daysOffset = 0

   def __init__(self, addr=None, causes=None, **kwargs):
      super().__init__(addr=addr, **kwargs)
      self.causes = causes or {}
      self.oldestTime = datetime.datetime(1970, 1, 1)
      self.inventory.addReloadCauseProvider(UcdReloadCauseProvider(self))

   def setRunTimeClock(self):
      diff = datetime.datetime.now() - self.oldestTime
      msecsInt = int(diff.seconds * 1000 + diff.microseconds / 1000)
      daysInt = diff.days
      daysInt += self.daysOffset
      msecsByte1 = (msecsInt >> 24) & 0xff
      msecsByte2 = (msecsInt >> 16) & 0xff
      msecsByte3 = (msecsInt >> 8) & 0xff
      msecsByte4 = msecsInt & 0xff
      daysByte1 = (daysInt >> 24) & 0xff
      daysByte2 = (daysInt >> 16) & 0xff
      daysByte3 = (daysInt >> 8) & 0xff
      daysByte4 = daysInt & 0xff
      data = [msecsByte1, msecsByte2, msecsByte3, msecsByte4,
              daysByte1, daysByte2, daysByte3, daysByte4]
      self.driver.setBlock(self.Registers.RUN_TIME_CLOCK, data)

   def getRunTimeClock(self):
      res = self.driver.getBlock(self.Registers.RUN_TIME_CLOCK)
      msecs = res[3] | (res[2] << 8) | (res[1] << 16) | (res[0] << 24)
      days = res[7] | (res[6] << 8) | (res[5] << 16) | (res[4] << 24)
      days -= self.daysOffset
      return self.oldestTime + datetime.timedelta(days=days, milliseconds=msecs)

   def getVersion(self):
      return self.driver.getVersion()

   def _getGpiFaults(self, reg):
      causes = []
      for name, typ in self.causes.items():
         if not isinstance(typ, UcdGpi):
            continue
         if reg & (1 << (typ.bit - 1)):
            causes.append(UcdReloadCauseEntry(
               cause=name,
               rcDesc='gpi fault',
               score=ReloadCauseScore.LOGGED |
                     ReloadCauseScore.getPriority(typ.priority),
            ))
      return causes

   def _parseFaultDetail(self, reg):
      msecs = (reg[0] << 24) | (reg[1] << 16) | (reg[2] << 8) | reg[3]
      fid = (reg[4] << 24) | (reg[5] << 16) | (reg[6] << 8) | reg[7]
      paged = (fid >> 31) & 0x1
      ftype = (fid >> 27) & 0xf
      page = ((fid >> 23) & 0xf) + 1
      days = fid & 0x7fffff
      value = (reg[9] << 8) | reg[8]
      return paged, ftype, page, value, days, msecs

   def _getFaultNum(self, reg):
      causes = []

      if len(reg) < self.Registers.LOGGED_FAULT_DETAIL_COUNT:
         logging.debug('invalid unknown cause %s', reg)
         return causes

      paged, ftype, page, value, days, msecs = self._parseFaultDetail(reg)
      days = int(days)
      secs = int(msecs / 1000)
      usecs = int((msecs - secs * 1000) * 1000)

      time = self.faultTimeBase + datetime.timedelta(days=days, seconds=secs,
                                                     microseconds=usecs)
      logging.debug('paged=%d type=%d page=%d value=0x%04x time=%s',
                    paged, ftype, page, value, time)

      if not paged and ftype == 9:
         # this is a Gpi
         for name, typ in self.causes.items():
            if isinstance(typ, UcdGpi) and typ.bit == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCauseEntry(
                  cause=name,
                  rcTime=datetimeToStr(time),
                  rcDesc='gpi detailed fault',
                  score=ReloadCauseScore.LOGGED | ReloadCauseScore.DETAILED |
                        ReloadCauseScore.getPriority(typ.priority),
               ))
      elif paged and ftype in [ 0, 1, 2 ]:
         # this is a Mon
         found = False
         for name, typ in self.causes.items():
            if isinstance(typ, UcdMon) and typ.val == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCauseEntry(
                  cause=name,
                  rcTime=datetimeToStr(time),
                  rcDesc='mon detailed fault',
                  score=ReloadCauseScore.LOGGED | ReloadCauseScore.DETAILED |
                        ReloadCauseScore.getPriority(typ.priority),
               ))
               found = True
         if not found:
            name = ['over-voltage', 'under-voltage', 'timeout-power-good'][ftype]
            cause = UcdReloadCauseEntry(
               cause=name,
               rcTime=datetimeToStr(time),
               rcDesc='%s on rail %d' % (name, page),
               score=ReloadCauseScore.EVENT | ReloadCauseScore.DETAILED |
                     ReloadCauseScore.getPriority(UcdPriority.NONE),
            )
            logging.debug('found: %s', cause.description)
            causes.append(cause)

      return causes

   def _getReloadCauses(self, drv):
      reg = drv.readFaults()
      if reg[ 0 ]:
         logging.debug('some non paged faults were detected')

      causes = []
      if self.gpiSize:
         gpi = 0
         for i in range(0, self.gpiSize):
            gpi |= reg[1 + i] << (8 * i)
         causes = self._getGpiFaults(gpi)
         logging.debug('found %d gpi faults', len(causes))
         for cause in causes:
            logging.debug('found: %s', cause)

      faultCount = drv.getFaultCount()
      logging.debug('found %d faults', faultCount)
      for i in range(0, faultCount):
         causes.extend(self._getFaultNum(drv.getFaultNum(i)))

      return causes

   def getReloadCauses(self):
      if inSimulation():
         return []

      with self.driver as drv:
         causes = self._getReloadCauses(drv)
         logging.debug('clearing faults')
         drv.clearFaults()

      return causes

class Ucd90160(Ucd):
   class Registers(Ucd.Registers):
      LOGGED_FAULTS_COUNT = 18

class Ucd90120(Ucd):
   gpiSize = 0

class Ucd90120A(Ucd):
   class Registers(Ucd.Registers):
      LOGGED_FAULTS_COUNT = 14

class Ucd90320(Ucd):
   class Registers(Ucd.Registers):
      LOGGED_FAULTS_COUNT = 37
      LOGGED_FAULT_DETAIL_COUNT = 12

   gpiSize = 4

   # The fault time is from 2000-01-01
   faultTimeBase = datetime.datetime(2000, 1, 1)
   # RUN_TIME_CLOCK is from 0001-01-01
   daysOffset = 719162    # Equals to 2000-01-01 - 0001-01-01

   def _parseFaultDetail(self, reg):
      pageAndMsecs = (reg[0] << 24) | (reg[1] << 16) | (reg[2] << 8) | reg[3]
      page = (pageAndMsecs >> 27) + 1
      msecs = pageAndMsecs & 0x7ffffff
      fid = (reg[4] << 24) | (reg[5] << 16) | (reg[6] << 8) | reg[7]
      paged = (fid >> 31) & 0x1
      ftype = (fid >> 27) & 0xf
      days = (fid >> 11) & 0xffff
      value = (reg[9] << 8) | reg[8]
      return paged, ftype, page, value, days, msecs

class Ucd9090A(Ucd):
   pass
