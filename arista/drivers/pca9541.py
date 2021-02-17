
import os
import time

from contextlib import closing

from ..core.driver import Driver
from ..core.utils import SMBus, inSimulation

from .kernel import I2cKernelDriver

CTRL_REG = 0x01

MYBUS = (1 << 0)
NMYBUS = (1 << 1)
BUSON = (1 << 2)
NBUSON = (1 << 3)
BUSINIT = (1 << 4)
TESTON = (1 << 6)
NTESTON = (1 << 7)

CTRL_CMDS = [0x4, 0x4, 0x5, 0x5, None, 0x4, 0x5, None, None, 0x0, 0x1, None, 0x0,
             0x0, 0x1, 0x1]

class Pca9541I2cDevDriver(Driver):
   def __init__(self, addr=None, **kwargs):
      super(Pca9541I2cDevDriver, self).__init__(**kwargs)
      self.addr = addr
      self.delay = 0.001 # 1ms

   def takeOwnership(self):
      try:
         with closing(SMBus(self.addr.bus)) as bus:
            count = 10
            while not self.arbitrate(bus) and count:
               time.sleep(self.delay)
               count -= 1
      except IOError:
         return False
      return count != 0

   def getCtrlReg(self, bus):
      return bus.read_byte_data(self.addr.address, CTRL_REG)

   def setCtrlReg(self, bus, value):
      bus.write_byte_data(self.addr.address, CTRL_REG, value)

   def arbitrate(self, bus):
      ctrl = self.getCtrlReg(bus)
      newCtrl = CTRL_CMDS[ctrl & 0xf]
      if newCtrl:
         self.setCtrlReg(bus, newCtrl)

      ctrl = self.getCtrlReg(bus)

      busOn = bool(ctrl & BUSON) ^ bool(ctrl & NBUSON)
      myBus = not bool(ctrl & MYBUS) ^ bool(ctrl & NMYBUS)

      return busOn and myBus

   def getBus(self):
      return self.addr.bus

   def ping(self):
      bus = SMBus(self.addr.bus)
      try:
         bus.read_byte(self.addr.address)
      except IOError:
         return False
      return True

class Pca9541KernelDriver(I2cKernelDriver):

   MODULE = 'i2c-mux-pca9541'
   NAME = 'pca9541'

   def getBus(self):
      if inSimulation():
         return 42
      channelPath = os.path.join(self.getSysfsPath(), 'channel-0')
      return self.busNameToId(os.path.basename(os.readlink(channelPath)))

   def ping(self):
      return True # TODO: linecard presence should not be based on pca

   def takeOwnership(self):
      return True
