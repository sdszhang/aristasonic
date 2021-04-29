#!/usr/bin/env python

from __future__ import print_function

import time

try:
   from arista.utils.sonic_platform.thermal import SfpThermal
   from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_Dom
   from sonic_platform_base.sfp_base import SfpBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

EEPROM_PATH = '/sys/class/i2c-adapter/i2c-{0}/{0}-{1:04x}/eeprom'

SFP_TYPE = 'SFP'
OSFP_TYPE = 'OSFP'

OSFP_TEMP_OFFSET = 14
OSFP_TEMP_WIDTH = 2
OSFP_THRESHOLD_OFFSET = 384
OSFP_THRESHOLD_WIDTH = 72

class Sfp(SfpBase):
   """
   Platform-specific sfp class
   """

   RESET_DELAY = 1

   def __init__(self, index, slot):
      SfpBase.__init__(self)
      self._index = index
      self._slot = slot
      self._sfputil = None
      sfp = slot.getXcvr()
      self._eepromPath = EEPROM_PATH.format(sfp.getI2cAddr().bus,
                                            sfp.getI2cAddr().address)
      self.sfp_type = sfp.getType().upper()
      self._thermal_list.append(SfpThermal(self))

   def get_id(self):
      return self._index

   def get_name(self):
      return self._slot.getName()

   def get_position_in_parent(self):
      return self._index

   def get_presence(self):
      return self._slot.getPresence()

   def is_replaceable(self):
      return True

   def get_status(self):
      return self.get_presence() and bool(self.get_transceiver_bulk_status())

   def get_lpmode(self):
      try:
         return self._slot.getLowPowerMode()
      except: # pylint: disable-msg=W0702
         return False

   def set_lpmode(self, lpmode):
      try:
         self._slot.setLowPowerMode(lpmode)
      except: # pylint: disable-msg=W0702
         return False
      return True

   def get_tx_disable(self):
      return self._slot.getTxDisable()

   def tx_disable(self, tx_disable):
      try:
         self._slot.setTxDisable(tx_disable)
      except: # pylint: disable-msg=W0702
         return False
      return True

   def get_reset_status(self):
      reset = self._slot.getReset()
      return reset.read() if reset else False

   def reset(self):
      try:
         self._slot.getReset().resetIn()
      except: # pylint: disable-msg=W0702
         return False
      time.sleep(self.RESET_DELAY)
      try:
         self._slot.getReset().resetOut()
      except: # pylint: disable-msg=W0702
         return False
      return True

   def get_temperature(self):
      bulkStatus = self.get_transceiver_bulk_status()
      return bulkStatus["temperature"] if bulkStatus else 0.0

   def clear_interrupt(self):
      intr = self._slot.getInterruptLine()
      if not intr:
         return False
      self.get_presence()
      intr.clear()
      return True

   def get_interrupt_file(self):
      intr = self._slot.getInterruptLine()
      if intr:
         return intr.getFile()
      return None

   # Some Sfp functionalities still come from sfputil
   def _get_sfputil(self):
      if not self._sfputil:
         import arista.utils.sonic_sfputil
         self._sfputil = arista.utils.sonic_sfputil.getSfpUtil()()
      return self._sfputil

   def get_transceiver_info(self):
      return self._get_sfputil().get_transceiver_info_dict(self._index)

   def _format_temps(self, val):
      # XXX: hack to format temps for supporting sfp thermals. Won't be needed
      # after sfp refactor is complete.
      if val.endswith('C'):
         temp = val.rstrip('C')
         numDecimals = len(temp.split('.')[1])
         if numDecimals > 3:
            temp = "{:.3f}".format(float(temp))
         return float(temp)
      return val

   def _format_bytes(self, data):
      # XXX: hack for converting bytes read from read_eeprom into format expected by
      # sonic_sfp parsers
      return ['%02x' % x for x in data]

   def get_transceiver_bulk_status(self):
      # XXX: SFP modules currently not supported
      if self.sfp_type == SFP_TYPE:
         return None
      # XXX: Hack to support thermals on OSFP/QSFP-DD modules
      elif self.sfp_type == OSFP_TYPE:
         tempRaw = self.read_eeprom(OSFP_TEMP_OFFSET, OSFP_TEMP_WIDTH)
         if not tempRaw:
            return None
         parser = qsfp_dd_Dom()
         domTemp = parser.parse_temperature(self._format_bytes(tempRaw), 0)
         bulkStatus = {
            'temperature': domTemp['data']['Temperature']['value']
         }
      else:
         bulkStatus = self._get_sfputil().get_transceiver_dom_info_dict(self._index)
      if isinstance(bulkStatus, dict):
         bulkStatus = {k: self._format_temps(v) for k, v in bulkStatus.items()}
      return bulkStatus

   def get_transceiver_threshold_info(self):
      # XXX SFP modules currently not supported
      if self.sfp_type == SFP_TYPE:
         return None
      # XXX: Hack to support thermals on OSFP/QSFP-DD modules
      elif self.sfp_type == OSFP_TYPE:
         threshRaw = self.read_eeprom(OSFP_THRESHOLD_OFFSET, OSFP_THRESHOLD_WIDTH)
         if not threshRaw:
            return None
         parser = qsfp_dd_Dom()
         domThresh = parser.parse_module_threshold_values(
                     self._format_bytes(threshRaw), 0)
         threshInfo = {
            'temphighalarm': domThresh['data']['TempHighAlarm']['value'],
            'temphighwarning': domThresh['data']['TempHighWarning']['value'],
            'templowalarm': domThresh['data']['TempLowAlarm']['value'],
            'templowwarning': domThresh['data']['TempLowWarning']['value']
         }
      else:
         threshInfo = self._get_sfputil().get_transceiver_dom_threshold_info_dict(
                      self._index)
      if isinstance(threshInfo, dict):
         threshInfo = {k: self._format_temps(v) for k, v in threshInfo.items()}
      return threshInfo

   def read_eeprom(self, offset, num_bytes):
      try:
         with open(self._eepromPath, mode='rb', buffering=0) as f:
            f.seek(offset)
            return bytearray(f.read(num_bytes))
      except (OSError, IOError):
         return None

   def write_eeprom(self, offset, num_bytes, write_buffer):
      try:
         with open(self._eepromPath, mode='r+b', buffering=0) as f:
            f.seek(offset)
            f.write(write_buffer[0:num_bytes])
      except (OSError, IOError):
         return False
      return True

