
try:
   from sonic_platform_base.component_base import ComponentBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e) from e

class Component(ComponentBase):
   def __init__(self, programmable):
      self.programmable = programmable

   def get_name(self):
      return str(self.programmable.getComponent())

   def get_presence(self):
      return True

   def get_model(self):
      return self.programmable.getComponent().__class__.__name__

   def get_serial(self):
      return 'N/A'

   def get_status(self):
      return True

   def get_description(self):
      return self.programmable.getDescription()

   def get_position_in_parent(self):
      return -1

   def is_replaceable(self):
      return False

   def get_firmware_version(self):
      return self.programmable.getVersion()

   def get_available_firmware_version(self, image_path):
      # pylint: disable=unused-argument
      # TODO: implement this API
      return self.get_firmware_version()

   def get_firmware_update_notification(self, image_path):
      # pylint: disable=unused-argument
      # TODO: implement this API
      return "None"

   def install_firmware(self, image_path):
      # pylint: disable=unused-argument
      # TODO: implement this API
      return True

   def update_firmware(self, image_path):
      # pylint: disable=unused-argument
      # TODO: implement this API
      return True

   def auto_update_firmware(self, image_path, boot_type):
      # pylint: disable=unused-argument
      # TODO: implement this API
      return 1
