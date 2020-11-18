#!/usr/bin/env python

from __future__ import print_function

try:
   from arista.utils.sonic_platform.fan_drawer import FanDrawer
   from arista.utils.sonic_platform.thermal import Thermal
   from sonic_platform_base.module_base import ModuleBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Module(ModuleBase):
   """
   Platform-specific class for interfacing with a module
   (supervisor module, line card module, etc. applicable for a modular chassis)
   """
   def __init__(self, sku):
      ModuleBase.__init__(self)
      self._fan_drawer_list = []
      self._sku = sku
      self._inventory = sku.getInventory()
      self._eeprom = sku.getEeprom()

      # Fan drawer APIs are missing for modules
      # Still add the FanDrawer object but also add the individual fans
      for slot in self._inventory.getFanSlots():
         self._fan_drawer_list.append(FanDrawer(self, slot))
      for drawer in self._fan_drawer_list:
         for fan in drawer.get_all_fans():
            self._fan_list.append(fan)

      for thermal in self._inventory.getTemps():
         self._thermal_list.append(Thermal(thermal))
      # TODO: Add Xcvrs? Only linecards have access to them

   def get_presence(self):
      return self._sku.getPresence()

   def get_model(self):
      return self._sku.getEeprom().get('SKU')

   def get_serial(self):
      return self._sku.getEeprom().get('SerialNumber')

   def get_status(self):
      # TODO: implement logic for this
      return True

   def is_replaceable(self):
      return True

   def get_base_mac(self):
      mac = self._sku.getEeprom().get('MAC')
      if mac is None:
         raise NotImplementedError
      return mac

   def get_system_eeprom_info(self):
      # TODO: prefdl to ONIE converter
      raise NotImplementedError

   def get_description(self):
      name = self._sku.getEeprom().get('SKU')
      if name is not None:
         return name
      return self._sku.getEeprom().get('SID', 'Unknown')

   def get_slot(self):
      return self._sku.getSlotId()

   def get_oper_status(self):
      # TODO: Implement the following modes
      #  - MODULE_STATUS_POWERED_DOWN
      #  - MODULE_STATUS_PRESENT
      #  - MODULE_STATUS_FAULT
      if not self.get_presence():
         return self.MODULE_STATUS_EMPTY
      if not self._sku.poweredOn():
         return self.MODULE_STATUS_OFFLINE
      if not self.get_status():
         return self.MODULE_STATUS_FAULT
      return self.MODULE_STATUS_ONLINE

   def reboot(self, reboot_type):
      # TODO: implement reboot mechanism
      return False

   def set_admin_state(self, up):
      # TODO: implement power on/off methods
      return False

   def get_maximum_consumed_power(self):
      pass

class SupervisorModule(Module):
   def get_name(self):
      mid = self._sku.getSlotId() - 1
      return '%s%s' % (self.MODULE_TYPE_SUPERVISOR, mid)

   def get_type(self):
      return self.MODULE_TYPE_SUPERVISOR

class FabricModule(Module):
   def get_name(self):
      return '%s%s' % (self.MODULE_TYPE_FABRIC, self._sku.getRelativeSlotId())

   def get_type(self):
      return self.MODULE_TYPE_FABRIC

class LinecardModule(Module):
   def get_name(self):
      return '%s%s' % (self.MODULE_TYPE_LINE, self._sku.getRelativeSlotId())

   def get_type(self):
      return self.MODULE_TYPE_LINE
