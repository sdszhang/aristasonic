
from ..core.component import Priority
from ..core.component.i2c import I2cComponent

from ..drivers.xcvr import (
   CmisEepromKernelDriver,
   SfpKernelDriver,
   QsfpKernelDriver,
   OsfpKernelDriver,
)

class Xcvr(I2cComponent):
   PRIORITY = Priority.DEFAULT

class CmisEeprom(Xcvr):
   DRIVER = CmisEepromKernelDriver

class Ethernet(Xcvr):
   pass

class Sfp(Xcvr):
   DRIVER = SfpKernelDriver

class Qsfp(Xcvr):
   DRIVER = QsfpKernelDriver

class Osfp(Xcvr):
   DRIVER = OsfpKernelDriver
