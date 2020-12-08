
from .kernel import I2cKernelDriver

class Max6658KernelDriver(I2cKernelDriver):
   MODULE = 'lm90'
   NAME = 'max6658'
