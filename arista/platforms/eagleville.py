
from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.utils import incrange

@registerPlatform()
class Eagleville(FixedSystem):

   SID = ['Eagleville']
   SKU = ['DCS-7050CX3M-32S']

   PORTS = PortLayout(
      qsfps=incrange(1, 32),
      sfps=incrange(33, 34),
   )

   def __init__(self):
      super(Eagleville, self).__init__()
