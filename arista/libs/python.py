
import sys

if sys.version_info.major == 2:
   PY_VERSION = 2
   def isinteger(value):
      return isinstance(value, (int, long))
else:
   PY_VERSION = 3
   def isinteger(value):
      return isinstance(value, int)
