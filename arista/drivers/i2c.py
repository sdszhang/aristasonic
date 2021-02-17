
from contextlib import closing

from ..accessors.gpio import FuncGpioImpl

from ..core.driver import Driver
from ..core import utils
from ..core.log import getLogger
from ..core.utils import SMBus

logging = getLogger(__name__)

class I2cDevDriver(Driver):

   REGISTER_CLS = None

   def __init__(self, name=None, addr=None, registerCls=None, **kwargs):
      super(I2cDevDriver, self).__init__(**kwargs)
      self.bus_ = None
      self.name = name
      self.addr = addr
      registerCls = registerCls or self.REGISTER_CLS
      self.regs = registerCls(self) if registerCls is not None else None
      # TODO:
      # introduce callback table based on value types used.

   def __str__(self):
      return '%s(addr=%s)' % (self.__class__.__name__, self.addr)

   @property
   def bus(self):
      if self.bus_ is None:
         self.bus_ = utils.SMBus(self.addr.bus)
      return self.bus_

   def close(self):
      if self.bus_ is not None:
         self.bus_.close()
         self.bus_ = None

   def smbusPing(self):
      try:
         with closing(SMBus(self.addr.bus)) as bus:
            bus.read_byte(self.addr.address)
      except IOError:
         return False
      return True

   def read_byte_data(self, reg):
      return self.bus.read_byte_data(self.addr.address, reg)

   def write_byte_data(self, reg, data):
      return self.bus.write_byte_data(self.addr.address, reg, data)

   def read_block_data(self, reg):
      if self.addr.supportSmbusBlock:
         return self.bus.read_block_data(self.addr.address, reg)
      data = self.bus.read_i2c_block_data(self.addr.address, reg)
      return data[1:data[0] + 1]

   def read_block_data_str(self, reg):
      return ''.join(chr(c) for c in self.read_block_data(reg))

   def read(self, reg):
      res = self.read_byte_data(reg)
      if res is None:
         raise IOError(self, reg)
      return res

   def write(self, reg, data):
      return self.write_byte_data(reg, data)

   def getGpio(self, attr, name=None):
      assert self.regs
      func = getattr(self.regs, attr)
      assert func
      name = name or attr
      # XXX: could be enhanced to forward all the appropriate info to the Gpio obj
      #      for now it's enough the way it is.
      return FuncGpioImpl(func, name)

   def __diag__(self, ctx):
      return {
         "name": self.name,
         "regs": self.regs.__diag__(ctx) if self.regs else None,
      }
