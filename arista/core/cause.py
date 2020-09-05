
from collections import defaultdict
import json
import os

from .config import Config
from .inventory import ReloadCause, ReloadCauseProvider
from .log import getLogger
from .utils import JsonStoredData

from ..descs.cause import ReloadCauseScore

from ..libs.date import datetimeToStr, strToDatetime
from ..libs.procfs import bootDatetime

logging = getLogger(__name__)

RELOAD_CAUSE_HISTORY_SIZE=128

class ReloadCauseEntry(ReloadCause):
   def __init__(self, cause='unknown', rcTime='unknown', rcDesc='',
                      score=ReloadCauseScore.EVENT):
      self.cause = cause
      self.time = rcTime
      self.description = rcDesc
      self.score = score

   def __str__(self):
      items = [self.cause]
      if self.description:
         items.append('description: %s' % self.description)
      if self.time != "unknown":
         items.append('time: %s' % self.time)
      return ', '.join(items)

   def getCause(self):
      return self.cause

   def getDescription(self):
      return self.description

   def getTime(self):
      return self.time

   def getScore(self):
      return self.score

   def toDict(self):
      return {
         'cause': self.cause,
         'time': self.time,
         'description': self.description,
         'score': self.score,
      }

   @classmethod
   def fromDict(cls, data):
      return cls(
         cause=data['cause'],
         rcTime=data['time'],
         rcDesc=data['description'],
         score=data['score'],
      )

class ReloadCauseProviderHelper(ReloadCauseProvider):
   def __init__(self, name='unknown', causes=None, extra=None):
      self.name = name
      self.causes = causes or []
      self.extra = extra or {}

   def getSourceName(self):
      return self.name

   def getCauses(self):
      return self.causes

   def getExtra(self):
      return self.extra

   def process(self):
      raise NotImplementedError

   def toDict(self):
      return {
         'name': self.getSourceName(),
         'causes': [c.toDict() for c in self.getCauses()],
         'extra': self.getExtra(),
      }

   @classmethod
   def fromDict(cls, data):
      return cls(
         name=data['name'],
         causes=[ReloadCauseEntry.fromDict(c) for c in data['causes']],
         extra=data['extra'],
      )

class ReloadCauseDataStore(JsonStoredData):
   def __init__(self, name=Config().reboot_cause_file, **kwargs):
      super(ReloadCauseDataStore, self).__init__(name,**kwargs)
      self.dataType = ReloadCauseEntry

   def convertFormatV1(self, data):
      for item in data:
         item['cause'] = item['reloadReason']
         del item['reloadReason']
      return data

   def maybeConvertReloadCauseFormat(self, data):
      assert isinstance(data, list) # TODO: use a dict to store data in the future
      if data and data[0].get('reloadReason'):
         data = self.convertFormatV1(data)
      return data

   def readCauses(self):
      data = self.maybeConvertReloadCauseFormat(self.read())
      return [self._createObj(item, self.dataType) for item in data]

   def writeCauses(self, causes):
      return self.writeList(causes)

class ReloadCauseReport(object):
   def __init__(self, date=None, cause=None, providers=None):
      self.date = date
      self.cause = cause
      self.providers = providers or []

   def processProviders(self, providers):
      for provider in providers:
         provider.process()
         self.providers.append(provider)

   def analyzeCauses(self):
      causes = defaultdict(list)
      for provider in self.providers:
         for cause in provider.getCauses():
            causes[cause.getScore()].append(cause)

      for _, causes in reversed(sorted(causes.items())):
         for cause in causes:
            # TODO: maybe sort causes by getTime but not that reliable
            self.cause = cause
            return

      self.cause = ReloadCauseEntry(
         cause='unknown',
         rcTime=datetimeToStr(self.date),
         rcDesc='could not find a valid reboot cause',
         score=ReloadCauseScore.UNKNOWN,
      )

   def toDict(self):
      return {
         'date': datetimeToStr(self.date),
         'cause': self.cause.toDict() if self.cause else None,
         'providers': [p.toDict() for p in self.providers],
      }

   @classmethod
   def fromDict(cls, data):
      return cls(
         date=strToDatetime(data['date']),
         cause=ReloadCauseEntry.fromDict(data['cause']),
         providers=[ReloadCauseProviderHelper.fromDict(p) for p in data['providers']]
      )

class ReloadCauseManager(object):

   VERSION = 3

   def __init__(self, name=None, path='/host/reboot-cause/platform/causes.json'):
      self.name = name
      self.path = path
      self.loaded = False
      self.reports = []

   @classmethod
   def processReportCause(cls, report):
      return report

   def readCauses(self, inventory, date=None):
      '''Read reload causes from hardware'''
      try:
         self.loadCauses()
      except Exception: # pylint: disable=broad-except
         logging.exception("Failed to read previous reboot causes")
      report = ReloadCauseReport(date=date or bootDatetime())
      report.processProviders(inventory.getReloadCauseProviders())
      report.analyzeCauses()
      # TODO: only add report if there is none for current boot
      #       probably a tempfile under /run/platform_cache/
      self.reports.insert(0, report)

   def fromDict(self, data):
      if data["version"] != self.VERSION:
         raise ValueError("Expected reload cause version to be %d" % self.VERSION)
      if data["name"] != self.name:
         raise ValueError("Expected reload cause name to match %s" % self.name)
      self.reports.extend(ReloadCauseReport.fromDict(d) for d in data['reports'])

   def loadCauseFile(self, path):
      if not os.path.exists(path):
         logging.debug("No prior reboot cause information from %s", path)
         return None

      with open(path) as f:
         try:
            return json.load(f)
         except (ValueError, KeyError):
            logging.exception("Failed to parse reboot cause from %s", self.path)

      return None

   def loadCauses(self):
      '''Load reload causes from file'''
      assert not self.loaded
      # TODO: tryLoadLegacy
      data = self.loadCauseFile(self.path)
      if data:
         self.fromDict(data)
      self.loaded = True

   def lastReport(self):
      if not self.reports:
         return None
      return self.reports[0]

   def allReports(self):
      return self.reports

   def toDict(self):
      return {
         'name': self.name,
         'reports': [r.toDict() for r in self.reports],
         'version': self.VERSION,
      }

   def storeCauses(self):
      '''Store reload causes into a file'''
      if not self.loaded:
         raise RuntimeError("Storing reboot cause without loading them first")
      with open(self.path, 'w') as f:
         json.dump(self.toDict(), f, indent=3, separators=(',', ': '))

def updateReloadCausesHistory(newCauses):
   rebootCauses = ReloadCauseDataStore(lifespan='persistent')
   causes = []
   if rebootCauses.exist():
      causes = rebootCauses.readCauses()
      for newCause in newCauses:
         addCause = True
         for cause in causes:
            if newCause.getTime() == cause.getTime() and \
                  newCause.getCause() == cause.getCause():
               addCause = False
               break
         if addCause:
            causes.append(newCause)
      rebootCauses.clear()
   else:
      causes = newCauses

   if len(causes) > RELOAD_CAUSE_HISTORY_SIZE:
      causes = causes[len(causes) - RELOAD_CAUSE_HISTORY_SIZE:]

   rebootCauses.writeList(causes)

def getReloadCause():
   rebootCauses = ReloadCauseDataStore()
   if rebootCauses.exist():
      return rebootCauses.readCauses()
   return None

def getReloadCauseHistory():
   rebootCauses = ReloadCauseDataStore(lifespan='persistent')
   if rebootCauses.exist():
      return rebootCauses.readCauses()
   return None
