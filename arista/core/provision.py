
import enum

class ProvisionMode(enum.IntEnum):
   NONE = 0
   STATIC = 1

   def __str__(self):
      return self.name.lower()
