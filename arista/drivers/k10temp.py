
from .kernel import PciKernelDriver

class K10TempKernelDriver(PciKernelDriver):
   MODULE = 'k10temp'
   PASSIVE = True
