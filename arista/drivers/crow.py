
from .kernel import I2cKernelDriver

class CrowFanCpldKernelDriver(I2cKernelDriver):
   MODULE = 'crow-fan-driver'
   NAME = 'crow_cpld'
