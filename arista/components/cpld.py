import time

from ..core.component import Priority
from ..core.component.i2c import I2cComponent
from ..core.driver import modprobe
from ..core.log import getLogger
from ..core.register import Register, RegisterMap

from ..drivers.cpld import SysCpldI2cDriver

from ..inventory.powercycle import PowerCycle

logging = getLogger(__name__)

class SysCpldCommonRegisters(RegisterMap):
   REVISION = Register(0x01, name='revision')
   SCRATCHPAD = Register(0x02, name='scratchpad', ro=False)
   SUICIDE = Register(0x03, name='suicide', ro=False)
   POWER_CYCLE = Register(0x04, name='powerCycle', ro=False)

class SysCpldPowerCycle(PowerCycle):
   def __init__(self, parent):
      self.parent = parent

   def powerCycle(self):
      # Modprobe for kdump kernel
      modprobe('i2c-dev')

      logging.info("Initiating powercycle through CPLD")
      self.parent.driver.regs.powerCycle(0xDE)
      logging.info("Powercycle triggered from CPLD")

class SysCpld(I2cComponent):
   DRIVER = SysCpldI2cDriver
   PRIORITY = Priority.DEFAULT

   def addPowerCycle(self):
      return self.inventory.addPowerCycle(SysCpldPowerCycle(self))

   def createPowerCycle(self):
      # TODO: deprecate this method in favor of addPowerCycle
      return self.addPowerCycle()

   def resetScd(self, sleep=1, wait=True):
      state = self.driver.regs.scdReset()
      logging.debug('%s: scd reset: %s', self, state)

      self.driver.regs.scdReset(1)
      if wait:
         time.sleep(sleep) # could be lower
      self.driver.regs.scdReset(0)

   def powerCycleOnSeu(self, value=None):
      return self.driver.regs.powerCycleOnCrc(value)

   def hasSeuError(self):
      return self.driver.regs.scdCrcError()

   def addGpio(self, attr, name=None):
      name = name or attr
      gpio = self.driver.getGpio(attr, name=name)
      self.inventory.addGpio(gpio)
      return gpio

   def addGpios(self, infos):
      gpios = []
      for info in infos:
         if isinstance(info, tuple):
            gpios.append(self.addGpio(*info))
         else:
            gpios.append(self.addGpio(info))
      return gpios

