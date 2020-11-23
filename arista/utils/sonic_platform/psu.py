#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.psu_base import PsuBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Psu(PsuBase):
   """
   Platform-specific PSU class
   """

   def __init__(self, psu):
      super(Psu, self).__init__()
      self._psu = psu

   def get_id(self):
      return self._psu.getId()

   def get_name(self):
      return self._psu.getName()

   def get_model(self):
      return self._psu.getModel()

   def get_serial(self):
      return self._psu.getSerial()

   def is_replaceable(self):
      return True

   def set_status_led(self, color):
      led = self._psu.getLed()
      if led is None:
         return True
      try:
         led.setColor(color)
      except Exception: # pylint: disable=broad-except
         return False
      return True

   def get_status_led(self, color=None):
      # TODO: remove color= argument
      led = self._psu.getLed()
      if led is None:
         return self.STATUS_LED_COLOR_OFF
      try:
         return led.getColor()
      except Exception: # pylint: disable=broad-except
         return self.STATUS_LED_COLOR_OFF

   def get_status(self):
      return self._psu.getStatus()

   def get_presence(self):
      return self._psu.getPresence()

   def get_powergood_status(self):
      return self.get_status()

   def get_interrupt_file(self):
      return None
