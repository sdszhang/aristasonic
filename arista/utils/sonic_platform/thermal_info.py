#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.sonic_thermal_control.thermal_info_base \
      import ThermalPolicyInfoBase
   from sonic_platform_base.sonic_thermal_control.thermal_json_object \
      import thermal_json_object
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class ThermalPolicyInfo(ThermalPolicyInfoBase):
   """
   Class for collecting chassis info to be fed to thermal policy
   """
   def collect(self, chassis):
      pass

@thermal_json_object("fan_info")
class FanInfo(ThermalPolicyInfo):
   def __init__(self):
      self.fans = {}
      self.fans_presence = {}
      self.fans_status = {}

   def _collect_fans(self, fans):
      for fan in fans:
         name = fan.get_name()
         self.fans[name] = fan
         self.fans_presence[name] = fan.get_presence()
         self.fans_status[name] = fan.get_status()

   def collect(self, chassis):
      if chassis.get_num_fan_drawers():
         for drawer in chassis.get_all_fan_drawers():
            self._collect_fans(drawer.get_all_fans())
      else:
         self._collect_fans(chassis.get_all_fans())

@thermal_json_object("thermal_info")
class ThermalInfo(ThermalPolicyInfo):
   def __init__(self):
      self.thermals = {}
      self.thermals_overheat = {}
      self.thermals_critical = {}

   def collect(self, chassis):
      for thermal in chassis.get_all_thermals():
         name = thermal.get_name()
         self.thermals[name] = thermal
         self.thermals_overheat[name] = thermal.sensor_overheat()
         self.thermals_critical[name] = thermal.sensor_critical()

@thermal_json_object("control_info")
class ControlInfo(ThermalPolicyInfo):
   def __init__(self):
      self.sensorsToFanSpeed = None

   def collect(self, chassis):
      self.sensorsToFanSpeed = chassis.getThermalControl().sensorsToFanSpeed
