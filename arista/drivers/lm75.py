
from .kernel import I2cKernelDriver

class Lm75KernelDriver(I2cKernelDriver):
   MODULE = 'lm75'
   NAME = 'lm75'

class Tmp75KernelDriver(Lm75KernelDriver):
   NAME = 'tmp75'
