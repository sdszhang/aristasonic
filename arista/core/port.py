
class Port(object):
   def __init__(self, index, speed, lanes):
      self.index = index
      self.speed = speed
      self.lanes = lanes

class PortLayout(object):
   def __init__(self, sfps=None, qsfps=None, osfps=None):
      self.sfpRange = sfps or []
      self.qsfpRange = qsfps or []
      self.osfpRange = osfps or []
      self.allRange = sorted(self.sfpRange + self.qsfpRange + self.osfpRange)

