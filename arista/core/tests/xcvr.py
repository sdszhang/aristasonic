from ...tests.testing import unittest

from ..fixed import FixedSystem
from ..utils import incrange
from ..xcvr import (
   OsfpSlot,
   QsfpSlot,
   SfpSlot,
   EthernetSlot,
)

from .mockinv import (
   MockGpio,
   MockInterrupt,
   MockLed,
   MockReset,
)

class MockOsfpSlot(OsfpSlot):
   pass

class MockQsfpSlot(QsfpSlot):
   pass

class MockSfpSlot(SfpSlot):
   pass

class MockEthernetSlot(EthernetSlot):
   pass

class MockFixedSystem(FixedSystem):
   def __init__(self, ethernetRange, sfpRange, qsfpRange, osfpRange):
      super().__init__()
      self.ethernetRange = ethernetRange
      self.sfpRange = sfpRange
      self.qsfpRange = qsfpRange
      self.osfpRange = osfpRange
      self.ethernetSlots = []
      self.sfpSlots = []
      self.qsfpSlots = []
      self.osfpSlots = []
      self.addrFunc = lambda addr : addr

      for i in ethernetRange:
         self.ethernetSlots.append(
            self.newComponent(
               MockEthernetSlot,
               slotId=i,
               leds=[MockLed()],
            )
         )

      for i in sfpRange:
         self.sfpSlots.append(
            self.newComponent(
               MockSfpSlot,
               slotId=i,
               addrFunc=self.addrFunc,
               interrupt=MockInterrupt(),
               presentGpio=MockGpio(),
               leds=[MockLed()],
               rxLosGpio=MockGpio(),
               txDisableGpio=MockGpio(),
               txFaultGpio=MockGpio()
            )
         )

      for i in qsfpRange:
         self.qsfpSlots.append(
            self.newComponent(
               MockQsfpSlot,
               slotId=i,
               addrFunc=self.addrFunc,
               presentGpio=MockGpio(),
               leds=[MockLed()],
               lpMode=MockGpio(),
               modSel=MockGpio(),
               reset=MockReset(),
            )
         )

      for i in osfpRange:
         self.osfpSlots.append(
            self.newComponent(
               MockOsfpSlot,
               slotId=i,
               addrFunc=self.addrFunc,
               presentGpio=MockGpio(),
               leds=[MockLed()],
               lpMode=MockGpio(),
               modSel=MockGpio(),
               reset=MockReset(),
            )
         )

class MockXcvrTest(unittest.TestCase):
   def _checkSystem(self, system):
      self.assertEqual(len(system.inventory.getEthernetSlots()),
                       len(system.ethernetRange))
      self.assertEqual(len(system.inventory.getSfpSlots()), len(system.sfpRange))
      self.assertEqual(len(system.inventory.getQsfpSlots()), len(system.qsfpRange))
      self.assertEqual(len(system.inventory.getOsfpSlots()), len(system.osfpRange))
      totalNumXcvrs = len(system.ethernetRange + system.sfpRange + system.qsfpRange +
                          system.osfpRange)
      self.assertEqual(len(system.inventory.getXcvrSlots()), totalNumXcvrs)

      for i, slot in zip(system.ethernetRange, system.ethernetSlots):
         self.assertEqual(slot.getId(), i)
         self._checkEthernet(slot)
      for i, slot in zip(system.sfpRange, system.sfpSlots):
         self.assertEqual(slot.getId(), i)
         self._checkSfp(slot)
      for i, slot in zip(system.qsfpRange, system.qsfpSlots):
         self.assertEqual(slot.getId(), i)
         self._checkQsfp(slot)
      for i, slot in zip(system.osfpRange, system.osfpSlots):
         self.assertEqual(slot.getId(), i)
         self._checkOsfp(slot)

   def _checkEthernet(self, ethernetSlot):
      self.assertIsNotNone(ethernetSlot.getXcvr())

   def _checkSfp(self, sfpSlot):
      self.assertIsNotNone(sfpSlot.getXcvr())

   def _checkQsfp(self, qsfpSlot):
      self.assertIsNotNone(qsfpSlot.getXcvr())

   def _checkOsfp(self, osfpSlot):
      self.assertIsNotNone(osfpSlot.getXcvr())

   def testXcvr(self):
      system = MockFixedSystem(ethernetRange=incrange(1, 10),
                               sfpRange=incrange(11, 20),
                               qsfpRange=incrange(21, 30),
                               osfpRange=incrange(31, 40))
      self._checkSystem(system)

if __name__ == '__main__':
   unittest.main()
