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

   def __init__(self, slot):
      super(Psu, self).__init__()
      self._slot = slot
      # TODO: add thermal info
      # TODO: add fan info
      # TODO: add power info

   def get_id(self):
      return self._slot.getId()

   def get_name(self):
      return self._slot.getName()

   def get_model(self):
      if not self.get_presence():
         return "N/A"
      return self._slot.getPsu().getModel()

   def get_serial(self):
      if not self.get_presence():
         return "N/A"
      return self._slot.getPsu().getSerial()

   def is_replaceable(self):
      return True

   def set_status_led(self, color):
      led = self._slot.getLed()
      if led is None:
         return True
      try:
         led.setColor(color)
      except Exception: # pylint: disable=broad-except
         return False
      return True

   def get_status_led(self, color=None):
      # TODO: remove color= argument
      led = self._slot.getLed()
      if led is None:
         return self.STATUS_LED_COLOR_OFF
      try:
         return led.getColor()
      except Exception: # pylint: disable=broad-except
         return self.STATUS_LED_COLOR_OFF

   def get_status(self):
      # TODO: check status of power supply itself
      return self._slot.getStatus()

   def get_presence(self):
      return self._slot.getPresence()

   def get_powergood_status(self):
      return self.get_status()

   def get_interrupt_file(self):
      return None
