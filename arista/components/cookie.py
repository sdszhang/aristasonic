import re

from ..core.cause import ReloadCauseEntry, ReloadCauseProviderHelper
from ..core.component.component import Component
from ..core.log import getLogger
from ..descs.cause import ReloadCausePriority, ReloadCauseScore
from ..drivers.cookie import CookieReloadCauseDriver
from ..libs.date import datetimeToStr, strToDatetime

logging = getLogger(__name__)

REBOOT_CMD_MSG_RE = re.compile(
   r"User issued '(?P<command>.+?)' command \[.*Time: (?P<time>.*)\]")

class CookiePriority(ReloadCausePriority):
   pass

class CookieReloadCauseEntry(ReloadCauseEntry):
   pass

class CookieReloadCauseProvider(ReloadCauseProviderHelper):
   def __init__(self, cookie):
      super().__init__(str(cookie))
      self.cookie = cookie

   def process(self):
      self.causes = self.cookie.getReloadCauses()

class CookieComponent(Component):
   DRIVER = CookieReloadCauseDriver

   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.inventory.addReloadCauseProvider(CookieReloadCauseProvider(self))

   def _fixTime(self, timestamp):
      # FIXME: The date format is locale-dependent
      try:
         dt = strToDatetime(timestamp, fmt='%a %d %b %Y %I:%M:%S %p %Z')
      except ValueError:
         try:
            dt = strToDatetime(timestamp, fmt='%a %b %d %H:%M:%S %Z %Y')
         except ValueError:
            return 'unknown'
      return datetimeToStr(dt)

   def getReloadCauses(self):
      causeStr = self.driver.getSoftwareCause()
      logging.debug('Got reboot cause from cookie file: %s', causeStr)
      if not causeStr:
         return []

      m = REBOOT_CMD_MSG_RE.match(causeStr)
      if m:
         logging.debug('Reboot cause is user reboot')
         return [
            CookieReloadCauseEntry(
               'reboot', self._fixTime(m.group('time')),
               rcDesc="User issued '{}' command".format(m.group('command')),
               score=ReloadCauseScore.LOGGED |
                     ReloadCauseScore.EVENT |
                     ReloadCauseScore.DETAILED |
                     ReloadCauseScore.getPriority(CookiePriority.HIGH))
         ]
      return []
