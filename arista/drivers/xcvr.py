import os

from .kernel import I2cKernelDriver

from ..core.utils import inSimulation

class XcvrKernelDriver(I2cKernelDriver):
   MODULE = 'optoe'

   def __init__(self, portName=None, **kwargs):
      super(XcvrKernelDriver, self).__init__(**kwargs)
      self.portName = portName

   def setup(self):
      super(XcvrKernelDriver, self).setup()

      if inSimulation():
         return

      portNamePath = os.path.join(self.getSysfsPath(), 'port_name')
      with open(portNamePath, 'w') as f:
         f.write(self.portName)

class SfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe2'

class QsfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe1'

class OsfpKernelDriver(XcvrKernelDriver):
   NAME = 'optoe3'
