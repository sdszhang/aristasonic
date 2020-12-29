
from contextlib import closing
import os

from ..core.driver import Driver
from ..core.utils import SMBus

from .kernel import I2cKernelDriver

class EepromKernelDriver(I2cKernelDriver):
   MODULE = 'eeprom'
   NAME = 'eeprom'

   def read(self):
      path = os.path.join(self.getSysfsPath(), 'eeprom')
      with open(path, 'rb') as f:
         return bytearray(f.read())

class SeepromI2cDevDriver(Driver):

   offset = 0
   length = 256
   header_size = 8

   def __init__(self, addr=None, **kwargs):
      super(SeepromI2cDevDriver, self).__init__(**kwargs)
      self.addr = addr

   def read(self):
      with closing(SMBus(self.addr.bus)) as bus:
         data = bytearray()
         bus.write_byte_data(self.addr.address, 0x00, 0)

         header = []
         # consecutive byte read
         for _ in range(self.offset, self.header_size):
            header += [bus.read_byte(self.addr.address)]

         # The 32 bits at 0x4 indicates the length of the prefdl (including the
         # header)
         length = ((header[4] << 24) |
                   (header[5] << 16) |
                   (header[6] << 8) |
                    header[7])

         data.extend(header)

         # consecutive byte read
         for _ in range(self.offset + self.header_size, length):
            data.append(bus.read_byte(self.addr.address))
         return data
