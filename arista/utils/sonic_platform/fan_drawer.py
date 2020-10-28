
try:
   from sonic_platform_base.fan_drawer_base import FanDrawerBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class FanDrawer(FanDrawerBase):
   def __init__(self, fan):
      # XXX: temporary 1:1 fan to fan_drawer mapping
      self._fan_list = [fan]

   def get_name(self):
      return self._fan_list[0].get_name()

   def get_status_led(self, color=None):
      return self._fan_list[0].get_status_led(color)

   def set_status_led(self, color):
      return self._fan_list[0].set_status_led(color)
