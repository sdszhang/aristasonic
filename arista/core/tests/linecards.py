
from __future__ import absolute_import, division, print_function

from ...tests.testing import unittest
from ...tests.logging import getLogger

from ...components.denali.card import DenaliCardSlot
from ...components.denali.linecard import DenaliLinecard
from ...components.linecard import Linecard
from ...components.scd import Scd
from ...core.card import LC_BASE_SLOTID

from ..card import CardSlot
from ..component import Priority
from ..platform import getPlatformSkus
from ..types import PciAddr

from ... import platforms as _

class LinecardTest(unittest.TestCase):
   @classmethod
   def setUpClass(cls):
      cls.logger = getLogger(cls.__name__)

   def createLinecard(self, cls):
      if issubclass(cls, DenaliLinecard):
         pci = PciAddr(bus=0x01)
         scd = Scd(PciAddr(bus=0x02))
         bus = scd.getSmbus(0x03)
         slot = DenaliCardSlot(None, LC_BASE_SLOTID, pci, bus)
      else:
         slot = CardSlot(None, 0)
      return cls(slot=slot)

   def testSetup(self):
      for name, linecardCls in getPlatformSkus().items():
         if not issubclass(linecardCls, Linecard):
            continue
         self.logger.info('Testing setup for linecard %s', name)
         linecard = self.createLinecard(linecardCls)
         assert linecard
         for f in [None, Priority.defaultFilter, Priority.backgroundFilter]:
            linecard.setup(filters=f)
         assert linecard

   def testClean(self):
      for name, linecardCls in getPlatformSkus().items():
         if not issubclass(linecardCls, Linecard):
            continue
         self.logger.info('Testing clean for linecard %s', name)
         linecard = self.createLinecard(linecardCls)
         assert linecard
         linecard.clean()
         assert linecard

class LinecardCpuTest(unittest.TestCase):
   @classmethod
   def setUpClass(cls):
      cls.logger = getLogger(cls.__name__)

   def testLinecardAsFixedSystem(self):
      for name, linecardCls in getPlatformSkus().items():
         if not issubclass(linecardCls, Linecard) or not linecardCls.CPU_CLS:
            continue
         self.logger.info('Testing linecard %s with CPU %s', name,
                          linecardCls.CPU_CLS)
         platform = linecardCls()
         platform.setup()
         platform.clean()

if __name__ == '__main__':
   unittest.main()
