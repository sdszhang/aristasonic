
from ..core.daemon import registerDaemonFeature, PollDaemonFeature
from ..core.log import getLogger

from ..components.dpm.pmbus import PmbusComponent

logging = getLogger(__name__)

@registerDaemonFeature()
class DpmMonitorFeature(PollDaemonFeature):

   NAME = 'dpm'
   INTERVAL = 4 * 60 * 60

   def init(self):
      PollDaemonFeature.init(self)
      self.devices = []
      for component in self.daemon.platform.iterComponents(filters=None):
         if isinstance(component, PmbusComponent):
            logging.info('%s: %s marked for periodic clock sync', self, component)
            self.devices.append(component)

   def callback(self, elapsed):
      for dpm in self.devices:
         dpm.setRunTimeClock()
