import copy

from ...core.register import Register, ClearOnReadRegister
from ...core.utils import inSimulation

class ScdResetRegister(Register):
   def __init__(self, addr, *fields, **kwargs):
      super(ScdResetRegister, self).__init__(addr, *fields, **kwargs)
      self.setAddr = addr
      self.clearAddr = addr + kwargs.get('clearOffset', 0x10)

   def writeBit(self, bitpos, value):
      if inSimulation():
         return

      if value:
         self.parent.write(self.setAddr, 1 << bitpos)
      else:
         self.parent.write(self.clearAddr, 1 << bitpos)

   def readBit(self, bitpos):
      if inSimulation():
         return 0

      return (self.parent.read(self.setAddr) >> bitpos) & 1

class ScdStatusChangedRegister(Register):
   def __init__(self, addr, *fields, **kwargs):
      super(ScdStatusChangedRegister, self).__init__(addr, *fields, **kwargs)

      fields = copy.deepcopy(fields)
      for field in fields:
         field.name = '%sChanged' % field.name
      self.changedRegister = ClearOnReadRegister(addr + 1, fields, **kwargs)

   def generateAttributes(self, parent=None):
      attrs = super(ScdStatusChangedRegister, self).generateAttributes(parent)
      attrs.update(self.changedRegister.generateAttributes(parent))
      return attrs
