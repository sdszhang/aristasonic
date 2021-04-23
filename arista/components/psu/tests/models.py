
from ....core.dynload import importSubmodules
from ....core.log import getLogger
from ....core.psu import PsuModel, PsuIdent

from ....descs.psu import PsuDesc

from ....tests.testing import unittest

logging = getLogger(__name__)

class PsuModelTest(unittest.TestCase):
   def _getAllPsuModels(self, pkg):
      modules = importSubmodules(pkg)
      models = []
      for name, module in modules.items():
         if '/tests/' in name:
            continue
         for value in module.__dict__.values():
            if isinstance(value, type) and issubclass(value, PsuModel) and \
               value != PsuModel:
               models.append(value)
      return models

   def assertValidI2cAddr(self, addr):
      self.assertGreater(addr, 3)
      self.assertLess(addr, 120)

   def _testPsuModel(self, model):
      if not model.IDENTIFIERS:
         logging.info('Skipping power supply base model %s' % model)
         return
      logging.info('Testing power supply model %s' % model)
      self.assertIsNotNone(model.MANUFACTURER)
      self.assertIsNotNone(model.IDENTIFIERS)
      identifiers = set()
      for ident in model.IDENTIFIERS:
         self.assertIsInstance(ident, PsuIdent)
         identifiers.add(ident.partName)
      self.assertEqual(len(identifiers), len(model.IDENTIFIERS))
      self.assertValidI2cAddr(model.IPMI_ADDR)
      self.assertValidI2cAddr(model.PMBUS_ADDR)
      self.assertGreater(model.CAPACITY, 0)
      self.assertIsInstance(model.DUAL_INPUT, bool)
      self.assertIsNotNone(model.PMBUS_CLS)
      if model.DRIVER is not None:
         self.assertIsInstance(model.DRIVER, str)
      self.assertIsInstance(model.DESCRIPTION, PsuDesc)

   def testPsuModels(self):
      models = self._getAllPsuModels('arista.components.psu')
      for model in models:
         self._testPsuModel(model)

if __name__ == '__main__':
   unittest.main()
