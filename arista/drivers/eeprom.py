
import os

from .kernel import I2cKernelDriver

class EepromKernelDriver(I2cKernelDriver):
   MODULE = 'eeprom'
   NAME = 'eeprom'

   def eepromPath(self):
      return os.path.join(self.getSysfsPath(), 'eeprom')

   def read(self, size=-1):
      with open(self.eepromPath(), 'rb') as f:
         return bytearray(f.read(size))

class At24KernelDriver(EepromKernelDriver):
   MODULE = 'at24'

class At24C64KernelDriver(At24KernelDriver):
   NAME = '24c64'

class At24C512KernelDriver(At24KernelDriver):
   NAME = '24c512'
