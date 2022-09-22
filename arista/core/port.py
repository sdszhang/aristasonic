from ..descs.xcvr import Osfp, Qsfp, Qsfp28, Rj45, Sfp

class PortLayout():
   def __init__(self, *args, **kwargs):
      self.ports = [p for pgen in args for p in pgen]
      if kwargs:
         self.ports += [Rj45(index) for index in kwargs.get('ethernets', [])]
         self.ports += [Sfp(index) for index in kwargs.get('sfps', [])]
         self.ports += [Osfp(index) for index in kwargs.get('osfps', [])]
         self.ports += [Qsfp28(index) for index in kwargs.get('qsfps', [])]
         self.ports.sort(key=lambda p: p.index)

   def getEthernets(self):
      return [p for p in self.ports if isinstance(p, Rj45)]

   def getSfps(self):
      return [p for p in self.ports if isinstance(p, Sfp)]

   def getQsfps(self):
      return [p for p in self.ports if isinstance(p, Qsfp)]

   def getOsfps(self):
      return [p for p in self.ports if isinstance(p, Osfp)]

   def getAllPorts(self):
      return self.ports

   def getPort(self, index):
      filtered = [p for p in self.ports if p.index == index]
      if not filtered:
         return None
      return filtered[0]

   @property
   def ethernetRange(self):
      return [p.index for p in self.getEthernets()]

   @property
   def sfpRange(self):
      return [p.index for p in self.getSfps()]

   @property
   def qsfpRange(self):
      return [p.index for p in self.getQsfps()]

   @property
   def osfpRange(self):
      return [p.index for p in self.getOsfps()]
