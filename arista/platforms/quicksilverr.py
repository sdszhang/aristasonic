
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.quirk import PciConfigQuirk
from ..core.utils import incrange

from ..descs.xcvr import Osfp, QsfpDD, Sfp

from .cpu.redstart import RedstartCpu

from .quicksilver import QuicksilverBase

# Hack for xcvrd to not crash, we probably want to do something better here
# Currently xcvrd will call into chassis.get_sfp() and sfp.get_something()
# which requires support for sysfs and whatnot
Fabric = Osfp

class QuicksilverRedstartBase(QuicksilverBase):
   SKU = []
   CPU_CLS = RedstartCpu

   def __init__(self):
      super().__init__()
      asicBridgeAddr = self.asic.addr.port.upstream.addr
      self.asic.quirks = [
         PciConfigQuirk(asicBridgeAddr, 'CAP_EXP+0x30.W=0x3',
                        'Force pcie link speed to Gen 3'),
         PciConfigQuirk(asicBridgeAddr, 'CAP_EXP+0x10.W=0x6',
                        'Trigger pcie link retraining'),
      ]

@registerPlatform()
class QuicksilverRedstartDd(QuicksilverRedstartBase):
   SID = [
      'Redstart8Mk2QuicksilverDD',
      'Redstart8Mk2NQuicksilverDD',
      'Redstart832Mk2QuicksilverDD',
      'Redstart832Mk2NQuicksilverDD',
   ]

   PORTS = PortLayout(
      (QsfpDD(i) for i in incrange(1, 16)),
      (Fabric(i) for i in incrange(17, 64)),
      (Sfp(i) for i in incrange(65, 66)),
   )

@registerPlatform()
class QuicksilverRedstartP(QuicksilverRedstartBase):
   SID = [
      'Redstart8Mk2QuicksilverP',
      'Redstart8Mk2NQuicksilverP',
      'Redstart832Mk2QuicksilverP',
      'Redstart832Mk2NQuicksilverP',
   ]

   PORTS = PortLayout(
      (Osfp(i) for i in incrange(1, 16)),
      (Fabric(i) for i in incrange(17, 64)),
      (Sfp(i) for i in incrange(65, 66)),
   )

   HAS_TH5_EXT_DIODE = False
