
from ..core.component import Component

class Max31790(Component):
   def __init__(self, addr, fans=None, **kwargs):
      super(Max31790, self).__init__(addr=addr, fans=fans, **kwargs)
