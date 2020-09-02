from ..core.register import Register

class PciRegister(Register):
   pass

class PciRegister8(PciRegister):
   def read(self):
      return self.parent.read8(self.addr)

   def write(self, value):
      return self.parent.write8(self.addr, value)

class PciRegister16(PciRegister):
   def read(self):
      return self.parent.read16(self.addr)

   def write(self, value):
      return self.parent.write16(self.addr, value)
