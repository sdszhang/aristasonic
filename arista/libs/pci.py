import os
import time

from ..core.log import getLogger
from ..core.utils import inSimulation
from ..core.types import PciAddr
from ..libs.wait import waitFor

logging = getLogger(__name__)

def pciRescan():
   logging.info('triggering kernel pci rescan')
   with open('/sys/bus/pci/rescan', 'w') as f:
      f.write('1')

def readSecondaryBus(pciAddr):
   if isinstance(pciAddr, PciAddr):
      pciAddr = str(pciAddr)

   '''Find secondary bus of a device with its PCI address.'''
   if inSimulation():
      bus = pciAddr.split(":")[1]
      return int(bus) + 1

   devPath = '/sys/bus/pci/devices/%s/secondary_bus_number' % pciAddr
   waitFor(lambda: os.path.exists(devPath), "Unable to get %s secondary bus" % pciAddr,
           timeout=60, sleep=True)

   def readBus():
      with open(devPath) as f:
          secondaryBus = int(f.readline())
      return secondaryBus

   def readAndCompareBus():
      # There is a bug where we try to read secondary bus number but kernel doesn't
      # completely write into the file. Double read to make sure thing is right.
      secondaryBus = readBus()
      time.sleep(0.1)
      return secondaryBus == readBus()

   waitFor(readAndCompareBus, description="Read and compare secondary bus fails")
   return readBus()
