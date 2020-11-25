from __future__ import absolute_import

from .sonic_utils import getInventory

from .. import platforms
from ..core import platform
from ..core.supervisor import Supervisor

try:
   from sonic_psu.psu_base import PsuBase
except ImportError as e:
   raise ImportError("%s - required module not found" % str(e))


def getPsuUtil():
   inventory = getInventory()

   class PsuUtil(PsuBase):
      """Platform-specific PsuUtil class"""

      def get_psu_presence(self, index):
         if index > inventory.getNumPsus() and index > 0:
            return False

         return inventory.getPsu(index-1).getPresence()

      def get_psu_status(self, index):
         if index > inventory.getNumPsus() and index > 0:
            return False

         return inventory.getPsu(index-1).getStatus()

      def get_num_psus(self):
         if isinstance(platform.getPlatform(), Supervisor):
            return platform.getPlatform().getChassis().NUM_PSUS
         return inventory.getNumPsus()

   return PsuUtil
