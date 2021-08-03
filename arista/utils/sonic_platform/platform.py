#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.platform_base import PlatformBase
   import arista.platforms
   from arista.core.platform import getPlatform
   from arista.utils.sonic_platform.chassis import Chassis
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Platform(PlatformBase):

   # NOTE: this cache is necessary since it's possible for some daemon or their
   #       dependencies to load the platform api multiple time.
   #       to avoid having different instances of the same platform API in a
   #       same daemon, the platform object is reused on subsequent invokations.
   PLATFORM_CACHE = {}

   def __init__(self):
      PlatformBase.__init__(self)
      platform = getPlatform()
      uid = platform.__class__.__name__
      pcache = Platform.PLATFORM_CACHE.get(uid)
      if pcache is not None:
         self._platform = pcache._platform
         self._chassis = pcache._chassis
      else:
         self._platform = platform
         self._chassis = Chassis(self._platform)
         Platform.PLATFORM_CACHE[uid] = self
