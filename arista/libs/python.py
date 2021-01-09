
import sys
import time

if sys.version_info.major == 2:
   PY_VERSION = 2
   def isinteger(value):
      return isinstance(value, (int, long))

   def monotonicRaw():
      return time.time()
else:
   PY_VERSION = 3
   def isinteger(value):
      return isinstance(value, int)

   def monotonicRaw():
      return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
