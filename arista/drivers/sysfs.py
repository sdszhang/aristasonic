from __future__ import division, print_function, with_statement

import os

from ..core.driver import Driver
from ..core import utils
from ..core.log import getLogger

from ..descs.led import LedColor

from ..inventory.fan import Fan
from ..inventory.led import Led
from ..inventory.xcvr import Xcvr

logging = getLogger(__name__)

class SysfsEntry(object):
   def __init__(self, parent, name, pathCallback=None):
      self.parent = parent
      self.driver = parent.driver
      self.name = name
      self.pathCallback = pathCallback or self.driver.getHwmonEntry
      self.entryPath_ = None

   @property
   def entryPath(self):
      if self.entryPath_ is None:
         self.entryPath_ = self.pathCallback(self.name)
      return self.entryPath_

   def exists(self):
      return os.path.exists(self.entryPath)

   def _readConversion(self, value):
      return str(value)

   def _writeConversion(self, value):
      return str(value)

   def _read(self):
      if utils.inSimulation():
         return '1'
      with open(self.entryPath, 'r') as f:
         return f.read()

   def _write(self, value):
      if utils.inSimulation():
         return
      with open(self.entryPath, 'w') as f:
         f.write(value)

   def read(self):
      return self._readConversion(self._read().rstrip())

   def write(self, value):
      self._write(self._writeConversion(value))

class SysfsEntryInt(SysfsEntry):
   def _readConversion(self, value):
      return int(value)

class SysfsEntryIntLinear(SysfsEntry):
   def __init__(self, parent, name, fromRange=None, toRange=None, **kwargs):
      super(SysfsEntryIntLinear, self).__init__(parent, name, **kwargs)
      self.fromRange = fromRange
      self.toRange = toRange

   def _linearConversion(self, value, fromRange, toRange):
      value -= fromRange[0]
      value *= toRange[1] - toRange[0]
      value //= fromRange[1]
      return value + toRange[0]

   def _readConversion(self, value):
      return self._linearConversion(int(value), self.fromRange, self.toRange)

   def _writeConversion(self, value):
      return str(self._linearConversion(int(value), self.toRange, self.fromRange))

class SysfsEntryBool(SysfsEntry):
   def _readConversion(self, value):
      return bool(int(value))

   def _writeConversion(self, value):
      return str(int(value))

class SysfsEntryCustomLed(SysfsEntry):
   def __init__(self, parent, name, value2color=None):
      self.value2color = value2color or {
         0 : LedColor.OFF,
         1 : LedColor.GREEN,
         2 : LedColor.RED,
         3 : LedColor.ORANGE,
      }
      self.color2value = { v : k for k, v in self.value2color.items() }
      def getLedPath(n):
         ledsPath = os.path.join(parent.driver.getSysfsPath(), 'leds')
         return os.path.join(ledsPath, n, 'brightness')
      super(SysfsEntryCustomLed, self).__init__(parent, name,
                                                pathCallback=getLedPath)

   def _readConversion(self, value):
      return self.value2color[int(value)]

   def _writeConversion(self, value):
      return str(self.color2value[value])

class FanSysfsImpl(Fan):

   MIN_FAN_SPEED = 30
   MAX_FAN_SPEED = 100

   def __init__(self, driver, desc, maxPwm=255, led=None, **kwargs):
      self.driver = driver
      self.desc = desc
      self.fanId = desc.fanId
      self.maxPwm = maxPwm
      self.led = led
      self.lastSpeed = None
      self.pwm = SysfsEntryIntLinear(self, 'pwm%d' % self.fanId,
                                     fromRange=(0, maxPwm), toRange=(0, 100))
      self.input = SysfsEntryInt(self, 'fan%d_input' % self.fanId)
      self.airflow = SysfsEntry(self, 'fan%d_airflow' % self.fanId)
      self.fault = SysfsEntryBool(self, 'fan%d_fault' % self.fanId)
      self.present = SysfsEntryBool(self, 'fan%d_present' % self.fanId)
      self.__dict__.update(kwargs)

   def getId(self):
      return self.fanId

   def getName(self):
      return 'fan%d' % self.fanId

   def getModel(self):
      return 'N/A'

   def getSpeed(self):
      return self.pwm.read()

   def getFault(self):
      if not self.fault.exists():
         return False
      return self.fault.read()

   def getStatus(self):
      return not self.getFault()

   def setSpeed(self, speed):
      if self.lastSpeed == self.MAX_FAN_SPEED and speed != self.MAX_FAN_SPEED:
         logging.debug("%s fan speed reduced from max", self.getName())
      elif self.lastSpeed != self.MAX_FAN_SPEED and speed == self.MAX_FAN_SPEED:
         logging.warn("%s fan speed set to max", self.getName())
      self.lastSpeed = speed
      return self.pwm.write(speed)

   def getPresence(self):
      if self.present.exists():
         return self.present.read()
      return self.input.read() != 0

   def getDirection(self):
      if self.airflow.exists():
         return self.airflow.read()
      return self.desc.airflow

   def getPosition(self):
      return self.desc.position if self.desc else 'N/A'

   def getLed(self):
      return self.led

class LedSysfsImpl(Led):
   def __init__(self, driver, desc, **kwargs):
      self.driver = driver
      self.desc = desc
      self.brightness = SysfsEntryCustomLed(self, desc.name)
      self.__dict__.update(kwargs)

   def getName(self):
      return self.desc.name

   def getColor(self):
      return self.brightness.read()

   def setColor(self, color):
      self.brightness.write(color)

   def isStatusLed(self):
      return 'sfp' in self.desc.name

class SysfsDriver(Driver):
   def __init__(self, sysfsPath=None, addr=None, **kwargs):
      self.sysfsPath = sysfsPath
      self.addr = addr
      super(SysfsDriver, self).__init__(**kwargs)

   def __str__(self):
      return '%s(path=%s, addr=%s)' % (self.__class__.__name__, self.sysfsPath,
                                       self.addr)

   def computeSysfsPath(self, gpio):
      if not self.sysfsPath:
         self.sysfsPath = utils.locateHwmonPath(
               self.addr.getSysfsPath(), gpio)

   def read(self, name, path=None):
      if utils.inSimulation():
         return '0'
      if not path and not self.sysfsPath:
         raise AttributeError
      path = path or os.path.join(self.sysfsPath, name)
      with open(path, 'r') as f:
         return f.read().rstrip()

   def write(self, name, value, path=None):
      if utils.inSimulation():
         return None
      if not path and not self.sysfsPath:
         raise AttributeError
      path = path or os.path.join(self.sysfsPath, name)
      with open(path, 'w') as f:
         return f.write(value)

class PsuSysfsDriver(SysfsDriver):
   def getPsuPresence(self, psu):
      gpio = 'psu%d_%s' % (psu.psuId, 'present')
      self.computeSysfsPath(gpio)
      return self.read(gpio) == '1'

   def getPsuStatus(self, psu):
      gpio = 'psu%d_%s' % (psu.psuId, 'status')
      self.computeSysfsPath(gpio)
      return self.read(gpio) == '1'

class XcvrSysfsDriver(SysfsDriver):
   def getXcvrPresence(self, xcvr):
      return self.read('%s_%s' % (xcvr.name, 'present')) == '1'

   def getXcvrLowPowerMode(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return False
      return self.read('%s_%s' % (xcvr.name, 'lp_mode')) == '1'

   def setXcvrLowPowerMode(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         return False
      return self.write('%s_%s' % (xcvr.name, 'lp_mode'), '1' if value else '0')

   def getXcvrModuleSelect(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return True
      return self.read('%s_%s' % (xcvr.name, 'modsel')) == '1'

   def setXcvrModuleSelect(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         return True
      logging.debug('setting modsel for %s to %s', xcvr.name, value)
      return self.write('%s_%s' % (xcvr.name, 'modsel'), '1' if value else '0')

   def getXcvrTxDisable(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return self.read('%s_%s' % (xcvr.name, 'txdisable')) == '1'
      return False

   def setXcvrTxDisable(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         logging.debug('setting txdisable for %s to %s', xcvr.name, value)
         return self.write('%s_%s' % (xcvr.name, 'txdisable'), '1' if value else '0')
      return False

class ResetSysfsDriver(SysfsDriver):
   def readReset(self, reset):
      return self.read('%s_%s' % (reset.name, 'reset'))

   def resetComponentIn(self, reset):
      logging.debug('putting %s in reset', reset.name)
      return self.write('%s_%s' % (reset.name, 'reset'), '1')

   def resetComponentOut(self, reset):
      logging.debug('putting %s out of reset', reset.name)
      return self.write('%s_%s' % (reset.name, 'reset'), '0')

class FanSysfsDriver(SysfsDriver):
   def __init__(self, maxPwm=255, addr=None, waitFile=None, waitTimeout=None,
                **kwargs):
      self.maxPwm = maxPwm
      self.addr = addr
      if waitFile == utils.WAITFILE_HWMON:
         waitFile = (self.addr.getSysfsPath(), 'hwmon', r'hwmon\d')
      self.fileWaiter = utils.FileWaiter(waitFile, waitTimeout)
      super(FanSysfsDriver, self).__init__(addr=addr, **kwargs)

   def setup(self):
      super(FanSysfsDriver, self).setup()
      self.fileWaiter.waitFileReady()

   # Fan speeds are a percentage
   def getFanSpeed(self, fan):
      self.computeSysfsPath('pwm%s' % fan.fanId)
      return int(float(self.read('pwm%s' % fan.fanId)) / self.maxPwm * 100)

   def setFanSpeed(self, fan, speed):
      self.computeSysfsPath('pwm%s' % fan.fanId)
      if not int(speed) in range(101):
         logging.error('invalid speed setting %s for fan %s', speed, fan.fanId)
         return None
      logging.debug('setting fan %s speed to %s', fan.fanId, speed)
      return self.write('pwm%s' % fan.fanId,
                        str(int(int(speed) * 0.01 * self.maxPwm)))

   def getFanDirection(self, fan):
      self.computeSysfsPath('pwm%s' % fan.fanId)
      return self.read('fan%s_airflow' % fan.fanId)

   def getFanPresence(self, fan):
      self.computeSysfsPath('pwm%s' % fan.fanId)
      return bool(int(self.read('fan%s_present' % fan.fanId)))

   def getFanStatus(self, fan):
      self.computeSysfsPath('pwm%s' % fan.fanId)
      try:
         return not bool(int(self.read('fan%s_fault' % fan.fanId)))
      except IOError:
         return self.getFanPresence(fan)

class LedSysfsDriver(SysfsDriver):
   def __init__(self, colorDict=None, **kwargs):
      self.colorDict = colorDict or {
         '0': LedColor.OFF,
         '1': LedColor.GREEN,
         '2': LedColor.RED,
         '3': LedColor.ORANGE,
      }
      self.inverseColorDict = {v: k for k, v in self.colorDict.items()}
      super(LedSysfsDriver, self).__init__(**kwargs)

   def getLedColor(self, led):
      path = os.path.join(self.sysfsPath, led.name, 'brightness')
      return self.colorDict[self.read(led.name, path=path)]

   def setLedColor(self, led, value):
      path = os.path.join(self.sysfsPath, led.name, 'brightness')
      if value in self.inverseColorDict:
         value = self.inverseColorDict[value]
      self.write(led.name, str(value), path=path)

class TempSysfsDriver(SysfsDriver):
   DEFAULT_MIN_VALUE = -20.0
   DEFAULT_MAX_VALUE = 120.0

   def __init__(self, waitFile=None, waitTimeout=None, **kwargs):
      self.fileWaiter = utils.FileWaiter(waitFile, waitTimeout)
      super(TempSysfsDriver, self).__init__(**kwargs)

   def readTemp(self, temp, name):
      # sysfs starts at one, mfg at 0
      gpio = 'temp%s_%s' % (temp.diode + 1, name)
      self.computeSysfsPath(gpio)
      return self.read(gpio)

   def writeTemp(self, temp, name, value):
      # sysfs starts at one, mfg at 0
      gpio = 'temp%s_%s' % (temp.diode + 1, name)
      self.computeSysfsPath(gpio)
      return self.write(gpio, str(value))

   def getTemperature(self, temp):
      return float(self.readTemp(temp, 'input')) / 1000

   def getPresence(self, temp):
      # Currently just rely on a valid temp reading
      try:
         return self.getTemperature(temp) > 0.0
      except AttributeError:
         return False

   def getLowThreshold(self, temp):
      try:
         return float(self.readTemp(temp, 'min')) / 1000
      except IOError:
         logging.debug('no temp%d_min' % (temp.diode + 1))
         return self.DEFAULT_MIN_VALUE

   def setLowThreshold(self, temp, value):
      try:
         return self.writeTemp(temp, 'min', int(value * 1000))
      except IOError:
         logging.debug('no temp%d_min' % (temp.diode + 1))
         return 0

   def getHighThreshold(self, temp):
      try:
         return float(self.readTemp(temp, 'max')) / 1000
      except IOError:
         logging.debug('no temp%d_crit' % (temp.diode + 1))
         return self.DEFAULT_MAX_VALUE

   def setHighThreshold(self, temp, value):
      try:
         return self.writeTemp(temp, 'max', int(value * 1000))
      except IOError:
         logging.debug('no temp%d_crit' % (temp.diode + 1))
         return 0
