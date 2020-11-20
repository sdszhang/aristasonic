
import re

from ..core.daemon import registerDaemonFeature, PollDaemonFeature
from ..core.log import getLogger
from ..core.supervisor import Supervisor

from ..descs.led import LedColor

logging = getLogger(__name__)

@registerDaemonFeature()
class StatusLedFeature(PollDaemonFeature):

   NAME = 'led'
   INTERVAL = 60

   def getActive(self, platform, led):
      return LedColor.GREEN

   def getStatus(self, platform, led):
      return LedColor.GREEN

   def getAllFansStatus(self, platform, led):
      for fan in platform.getInventory().getFans():
         if not fan.getStatus():
            return LedColor.RED
      return LedColor.GREEN

   def getAllPsusStatus(self, platform, led):
      for psu in platform.getInventory().getPsus():
         if psu.getPresence() and not psu.getStatus():
            return LedColor.RED
      return LedColor.GREEN

   def getAllLinecardsStatus(self, platform, led):
      assert isinstance(platform, Supervisor)
      # TODO: implement card fault check
      return LedColor.GREEN

   def getAllFabricsStatus(self, platform, led):
      assert isinstance(platform, Supervisor)
      # TODO: implement card fault check
      return LedColor.GREEN

   def getLedPolicy(self, led):
      name = led.getName()
      ledPolicies = {
         'active': self.getActive,
         'status': self.getStatus,
         'fan_status': self.getAllFansStatus,
         'psu_status': self.getAllPsusStatus,
         'fabric_status': self.getAllFabricsStatus,
         'linecard_status': self.getAllLinecardsStatus,
      }
      policy = ledPolicies.get(name)
      return policy

   def callback(self, elapsed):
      inventory = self.daemon.platform.getInventory()

      for led in inventory.getLeds().values():
         policy = self.getLedPolicy(led)
         if policy is None:
            continue

         try:
            color = policy(self.daemon.platform, led)
         except Exception: # pylint: disable=broad-except
            logging.error("failed apply policy for led %s", led)
            continue

         try:
            led.setColor(color)
         except Exception: # pylint: disable=broad-except
            logging.error("failed to set led color %s for %s", color, led)
            continue
