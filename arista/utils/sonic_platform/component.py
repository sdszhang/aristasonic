
try:
   from sonic_platform_base.component_base import ComponentBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e) from e

class Component(ComponentBase):
   def __init__(self, programmable):
      self.programmable = programmable

   def get_name(self):
      return str(self.programmable.getComponent())

   def get_description(self):
      return self.programmable.getDescription()

   def get_firmware_version(self):
      return self.programmable.getVersion()

   def get_available_firmware_version(self, image_path):
      raise NotImplementedError

   def get_firmware_update_notification(self, image_path):
      raise NotImplementedError

   def install_firmware(self, image_path):
      raise NotImplementedError

   def update_firmware(self, image_path):
      raise NotImplementedError

   def auto_update_firmware(self, image_path, boot_type):
      raise NotImplementedError
