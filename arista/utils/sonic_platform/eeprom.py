#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.sonic_eeprom.eeprom_base import EepromDecoder
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Eeprom(EepromDecoder):
   """
   Platform-specific Eeprom class
   """

   def __init__(self, prefdl, **kwargs):
      EepromDecoder.__init__(self, path=None, eepromFormat=None, start=0, status='',
                             readOnly=True, **kwargs)
      self._prefdl = prefdl

   def read_eeprom(self):
      return self._prefdl
