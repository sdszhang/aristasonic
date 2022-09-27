
from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout

@registerPlatform()
class Eagleville(FixedSystem):

   SID = ['Eagleville']
   SKU = ['DCS-7050CX3M-32S']

   PORTS = PortLayout()

   def __init__(self):
      super(Eagleville, self).__init__()
