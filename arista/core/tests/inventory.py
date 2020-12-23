
from __future__ import absolute_import, division, print_function

from ...tests.testing import unittest

from ..inventory import Inventory
from ..metainventory import MetaInventory, LazyInventory

from .mockinv import (
   MockFan,
   MockInterrupt,
   MockLed,
   MockPhy,
   MockPowerCycle,
   MockPsu,
   MockPsuSlot,
   MockReset,
   MockSlot,
   MockTemp,
   MockWatchdog,
   MockXcvr,
)

class InventoryTest(unittest.TestCase):
   def _populateTestInventory(self, inv):
      inv.addPorts(
         sfps=list(range(0, 2)),
         qsfps=list(range(2, 4)),
         osfps=list(range(4, 6)),
      )
      xcvrs = [
         MockXcvr(0, MockXcvr.SFP, "SFP-1G-SX"),
         MockXcvr(1, MockXcvr.SFP, "CAB-SFP-SFP-1M"),
         MockXcvr(2, MockXcvr.QSFP, "CAB-Q-Q-100G-1M"),
         MockXcvr(3, MockXcvr.QSFP, "QSFP-100G-CWDM4"),
         MockXcvr(4, MockXcvr.OSFP, "AB-O-O-400G-1M"),
         MockXcvr(5, MockXcvr.OSFP, "AOC-O-O-400G-3M"),
      ]
      for xcvr in xcvrs:
         led = MockLed('%s%d' % (xcvr.typeStr(xcvr.xcvrType), xcvr.portId))
         inv.addLed(led)
         inv.addXcvr(xcvr)

      inv.addResets({
         'internet': MockReset('internet'),
         'humanity': MockReset('humanity'),
      })
      psus = inv.addPsus([
         MockPsu(1, 'psu1'),
         MockPsu(2, 'psu2'),
      ])
      for psu in psus:
         inv.addPsuSlot(MockPsuSlot(psu.psuId, name=psu.getName(), psu=psu))
      inv.addFans([
         MockFan(1, 'fan1'),
         MockFan(2, 'fan2'),
         MockFan(3, 'fan3'),
         MockFan(4, 'fan4'),
      ])
      inv.addPowerCycle(MockPowerCycle())
      inv.addWatchdog(MockWatchdog())
      inv.addInterrupt(MockInterrupt('intr'))
      inv.addPhy(MockPhy())
      inv.addSlot(MockSlot())
      inv.addTemp(MockTemp(diode=1))
      inv.addTemp(MockTemp(diode=2))

   def _populateSmallTestInventory(self, inv):
      inv.addPsus([
         MockPsu(3, 'psu3'),
         MockPsu(4, 'psu4'),
      ])

   def _getTestInventory(self, populate=True):
      inv = Inventory()
      if populate:
         self._populateTestInventory(inv)
      return inv

   def _getSmallInventory(self):
      inv = self._getTestInventory(populate=False)
      self._populateSmallTestInventory(inv)
      return inv

   def _getFullInventory(self):
      inv = self._getTestInventory()
      self._populateSmallTestInventory(inv)
      return inv

   def _getTestMetaInventory(self, ):
      inv = self._getTestInventory()
      meta = MetaInventory(invs=[inv])
      return meta

   def _iterInventoryGetters(self):
      for attr in dir(Inventory):
         if attr.startswith('get') and attr.endswith( 's' ):
            yield attr

   def assertInventoryEqual(self, inv1, inv2):
      for attr in self._iterInventoryGetters():
         v1 = getattr(inv1, attr)()
         v2 = getattr(inv2, attr)()
         self.assertEqual(type(v1), type(v2))
         if isinstance(v1, (list, dict, set)):
            for item in v1:
               self.assertIn(item, v2)
         else:
            self.assertEqual(v1, v2)

   def testInventory(self):
      inv = self._getTestInventory()
      inv.getXcvrs()

   def testSimpleMetaInventory(self):
      meta = self._getTestMetaInventory()
      with self.assertRaises(AttributeError):
         meta.nonExistant()
      self.assertDictEqual(meta.getXcvrs(), meta.invs[0].getXcvrs())

   def testGeneratorMetaInventory(self):
      inv1 = self._getTestInventory()
      inv2 = self._getSmallInventory()
      invs = self._getFullInventory()

      def generator():
         for inv in [ inv1, inv2 ]:
            yield inv

      meta = MetaInventory(invs=iter(generator()))
      self.assertListEqual(meta.getPsus(), invs.getPsus())

   def testLazyInventory(self):
      lazy = LazyInventory()
      self.assertEqual(len(lazy.__dict__), 0)
      self._populateTestInventory(lazy)
      self.assertNotEqual(len(lazy.__dict__), 0)

      inv = self._getTestInventory()
      self.assertGreaterEqual(len(inv.__dict__), len(lazy.__dict__))

   def testLazyMetaInventory(self):
      lazy1 = LazyInventory()
      self._populateTestInventory(lazy1)
      # lazyLen1 = len(lazy1.__dict__)
      lazy2 = LazyInventory()
      self._populateSmallTestInventory(lazy2)
      # lazyLen2 = len(lazy2.__dict__)
      meta = MetaInventory(invs=[lazy1, lazy2])

      inv = self._getFullInventory()
      self.assertInventoryEqual(inv, meta)

      # self.assertEqual(lazyLen1, len(lazy1.__dict__))
      # self.assertEqual(lazyLen2, len(lazy2.__dict__))

   def testLegacyLazyMetaInventory(self):
      inv = self._getTestInventory()
      lazy = LazyInventory()
      self._populateSmallTestInventory(lazy)
      meta = MetaInventory(invs=[inv, lazy])

      inv = self._getFullInventory()
      self.assertInventoryEqual(inv, meta)

   def testEmptyMetaInventory(self):
      meta = MetaInventory()
      inv = Inventory()
      for attr in self._iterInventoryGetters():
         metaval = getattr(meta, attr)()
         invval = getattr(inv, attr)()
         self.assertEqual(metaval, invval)

if __name__ == '__main__':
   unittest.main()
