
from .kernel import I2cKernelDriver

class XcvrKernelDriver(I2cKernelDriver):
   MODULE = 'optoe'

class SfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe2'

class QsfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe1'

class OsfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe3'
