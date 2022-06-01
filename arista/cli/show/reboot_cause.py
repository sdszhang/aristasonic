
from __future__ import print_function

from ...core.cause import getReloadCauseManager

from . import Renderer

class ShowRebootCause(Renderer):

   NAME = 'reboot-cause'

   def getData(self, show):
      rcm = getReloadCauseManager(show.platforms[0])
      if show.args.history:
         return [rp.toDict() for rp in rcm.allReports()]
      else:
         rp = rcm.lastReport()
         return [rp.toDict()] if rp else []

   def _renderCauseText(self, cause, prefix=''):
      if cause['time'] != 'unknown':
         prefix = f"{prefix}{cause['time']} "
      print('%s%s (%s)' % (prefix, cause['cause'], cause['description']))

   def _renderProviderText(self, report):
      for provider in report['providers']:
         print('  %s' % provider['name'])
         for cause in provider['causes']:
            self._renderCauseText(cause, prefix='   - ')

   def renderText(self, show):
      data = self.data(show)
      for rp in data:
         self._renderCauseText(rp['cause'])
         if show.args.all:
            self._renderProviderText(rp)
