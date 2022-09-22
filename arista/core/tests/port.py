from ...core.utils import incrange
from ...descs.xcvr import Osfp, Qsfp, Rj45, Sfp, Xcvr
from ...tests.testing import unittest
from ..port import PortLayout

class PortLayoutTest(unittest.TestCase):
   def _checkPortLayout(self, portLayout):
      self.assertEqual(len(portLayout.ethernetRange), 8)
      self.assertEqual(len(portLayout.sfpRange), 8)
      self.assertEqual(len(portLayout.qsfpRange), 8)
      self.assertEqual(len(portLayout.osfpRange), 8)

      ports = portLayout.getAllPorts()
      for p in ports:
         self.assertIsInstance(p, Xcvr)

      families = [Rj45, Sfp, Qsfp, Osfp]
      for p in ports:
         self.assertTrue(isinstance(p, families[(p.index - 1) // 8]))

      indexes = [p.index for p in ports]
      self.assertListEqual(indexes, sorted(indexes))

      self.assertEqual(len(ports), len(set(indexes)))
      self.assertEqual(1, min(indexes))
      self.assertEqual(len(ports), max(indexes))

   def testStructure(self):
      portLayout = PortLayout(
         ethernets=incrange(1, 8),
         sfps=incrange(9, 16),
         qsfps=incrange(17, 24),
         osfps=incrange(25, 32),
      )
      self._checkPortLayout(portLayout)

      portLayout = PortLayout(
         (Rj45(i) for i in incrange(1, 8)),
         (Sfp(i) for i in incrange(9, 16)),
         (Qsfp(i) for i in incrange(17, 24)),
         (Osfp(i) for i in incrange(25, 32)),
      )
      self._checkPortLayout(portLayout)
