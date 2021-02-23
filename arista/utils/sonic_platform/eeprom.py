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

   # Work in progress
   def __init__(self, prefdl):
      EepromDecoder.__init__(self)
      self._prefdl = prefdl
