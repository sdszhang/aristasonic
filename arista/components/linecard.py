
from ..core.card import Card
from ..core.provision import ProvisionMode

class LCpuCtx(object):
   def __init__(self, provision=ProvisionMode.NONE):
      self.provision = provision

class Linecard(Card): # pylint: disable=abstract-method
   pass
