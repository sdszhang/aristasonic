
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc
from ..core.cooling import Airflow

class FanPosition(object):
   UNKNOWN = 'unknown'
   INLET = 'inlet'
   OUTLET = 'outlet'

class FanDesc(HwDesc):
   def __init__(self, fanId, position=FanPosition.UNKNOWN, airflow=Airflow.UNKNOWN,
                ledId=None, **kwargs):
      super(FanDesc, self).__init__(**kwargs)
      self.fanId = fanId
      self.ledId = ledId
      self.position = position
      self.airflow = airflow

class FanSlotDesc(HwDesc):
   def __init__(self, slotId, name=None, fans=None, ledId=None, **kwargs):
      super(FanSlotDesc, self).__init__(**kwargs)
      self.slotId = slotId
      self.name = name
      self.fans = fans
