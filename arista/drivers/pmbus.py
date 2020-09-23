import os

from ..core.driver import Driver
from ..core.utils import simulateWith
from ..core.log import getLogger

from .i2c import I2cDevDriver

logging = getLogger(__name__)

class PsuPmbusDetect(I2cDevDriver):

   MFR_ID = 0x99
   MFR_MODEL = 0x9a
   MFR_REVISION = 0x9b
   MFR_LOCATION = 0x9c
   MFR_DATE = 0x9d
   MFR_SERIAL = 0x9e

   def __init__(self, addr):
      super(PsuPmbusDetect, self).__init__(name='pmbus-detect', addr=addr)
      self.addr = addr
      self.id_ = None
      self.model_ = None
      self.revision_ = None
      self.location_ = None
      self.date_ = None
      self.serial_ = None

   def id(self):
      if self.id_ is None:
         self.id_ = self.read_block_data_str(self.MFR_ID)
      return self.id_

   def model(self):
      if self.model_ is None:
         self.model_ = self.read_block_data_str(self.MFR_MODEL)
      return self.model_

   def revision(self):
      if self.revision_ is None:
         self.revision_ = self.read_block_data_str(self.MFR_REVISION)
      return self.revision_

   def location(self):
      if self.location_ is None:
         self.location_ = self.read_block_data_str(self.MFR_LOCATION)
      return self.location_

   def date(self):
      if self.date_ is None:
         self.date_ = self.read_block_data_str(self.MFR_DATE)
      return self.date_

   def serial(self):
      if self.serial_ is None:
         self.serial_ = self.read_block_data_str(self.MFR_SERIAL)
      return self.serial_

   def getMetadata(self):
      return {
         'id': self.id(),
         'model': self.model(),
         'revision': self.revision(),
         'location': self.location(),
         'date': self.date(),
         'serial': self.serial(),
      }

class PmbusDriver(Driver):
   def __init__(self, addr=None, hwmonDir=None, sensors=None, **kwargs):
      self.addr = addr
      self.hwmonDir = hwmonDir
      self.sensors = sensors or []
      super(PmbusDriver, self).__init__(**kwargs)

   def sensorPath(self, name):
      return os.path.join(self.hwmonDir, name)

   def readSensor(self, name):
      path = self.sensorPath(name)
      if not os.path.exists(path):
         logging.debug('hwmon sensor %s does not exist', path)
         return 0, False
      logging.debug('hwmon-read %s', path)
      with open(path, 'r') as f:
         return int(f.read()), True

   def getStatusSim_(self):
      logging.info('reading psu status from hwmon: %s', self.hwmonDir)
      return True

   @simulateWith(getStatusSim_)
   def getPsuStatus(self, psu):
      # At least one sensor is expected to exist, otherwise treat it as a failure.
      # Check input and output values of current and voltage are in the range.

      # The PMBus PSU will be temporarily used as a generic PSU, so we will fallback
      # to relying on psu presence if the PSU model does not use PMBus
      sensorExists = False

      for sensor in self.sensors:
         nonZero = False
         # The value must be non zero.
         value, exists = self.readSensor('%s_input' % sensor)
         if exists:
            sensorExists = True
         else:
            continue
         if not value:
            continue
         nonZero = True

         # The value must be lower than its critical value.
         valueCrit, exists = self.readSensor('%s_crit' % sensor)
         if exists and valueCrit > 0 and value > valueCrit:
            return False

         # The value must be greater than its lowest allowed value.
         valueLCrit, exists = self.readSensor('%s_lcrit' % sensor)
         if exists and value < valueLCrit:
            return False

         # Not all PSUs will have all the curr/in values, so we just need one
         if nonZero:
            return True

      if sensorExists:
         return False
      return psu.getPresence()
