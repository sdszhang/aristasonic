
class ReloadCauseScore(object):
   # DO NOT CHANGE EXISTING VALUES UNLESS YOU UNDERSTAND THE IMPLICATIONS
   # format:
   # 0:7 -> priority
   UNKNOWN = 0
   DETAILED = (1 << 10)
   EVENT = (1 << 16)
   LOGGED = (1 << 32)

   @staticmethod
   def getPriority(value):
       assert value == (value & 0xff)
       return value & 0xff
