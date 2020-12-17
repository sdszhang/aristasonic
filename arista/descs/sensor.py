
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class Position(object):
   INLET = 'inlet'
   OUTLET = 'outlet'
   OTHER = 'other'

class SensorDesc(HwDesc):
   def __init__(self, diode, name, position, target, overheat, critical,
                low=-10.0, lcritical=-20.0, **kwargs):
      super(SensorDesc, self).__init__(**kwargs)
      self.diode = diode
      self.fmt = name
      self.name = name
      self.position = position
      self.target = float(target)
      self.overheat = float(overheat)
      self.critical = float(critical)
      self.low = float(low)
      self.lcritical = float(lcritical)

   def renderName(self, **kwargs):
      values = kwargs.copy()
      values.update(self.__dict__)
      self.name = self.fmt % values
