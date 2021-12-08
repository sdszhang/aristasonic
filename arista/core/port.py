
class Port():
   def __init__(self, index, speed, lanes):
      self.index = index
      self.speed = speed
      self.lanes = lanes

class PortLayout():
   def __init__(self, ethernets=None, sfps=None, qsfps=None, osfps=None):
      self.ethernetRange = ethernets or []
      self.sfpRange = sfps or []
      self.qsfpRange = qsfps or []
      self.osfpRange = osfps or []
      self.allRange = sorted(self.ethernetRange + self.sfpRange + self.qsfpRange +
                             self.osfpRange)
