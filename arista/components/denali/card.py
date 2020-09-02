
from __future__ import absolute_import, division, print_function

import copy

from ...core.card import Card, CardSlot
from ...core.log import getLogger
from ...libs.pci import pciRescan
from ...libs.wait import waitFor
from ..dpm import Ucd90320
from ..eeprom import PrefdlSeeprom
from ..pca9541 import Pca9541
from ..power import PowerDomain

logging = getLogger(__name__)

class DenaliCard(Card):
   def __init__(self, *args, **kwargs):
      self.scd = None
      self.pca = None
      self.eeprom = None
      self.standbyUcd = None
      self.plx = None
      self.asics = []
      self.gpio1 = None
      self.gpio2 = None
      super(DenaliCard, self).__init__(*args, **kwargs)

   def getEeprom(self):
      try:
         return self.eeprom.prefdl()
      except Exception: # pylint: disable=broad-except
         logging.debug("%s: failed to read eeprom", self)
         return {}

   def createGpio1(self):
      self.gpio1 = None

   def createPlx(self):
      self.plx = None

   def createAsics(self):
      self.asics = []

   def createScd(self):
      self.scd = None

   def standbyCommon(self):
      '''Define Mux, Prefdl eeprom, Gpio1, Dpm, Pols, Temp sensors,
         and Fans...
      '''
      self.standby = self.newComponent(PowerDomain)
      self.pca = self.standby.newComponent(Pca9541, self.slot.bus.i2cAddr(0x77))
      self.eeprom = self.standby.newComponent(PrefdlSeeprom,
                                              self.slot.bus.i2cAddr(0x50))
      self.standbyUcd = self.standby.newComponent(Ucd90320,
                                                  self.slot.bus.i2cAddr(0x11))
      self.createGpio1()
      self.createPlx()

   def standbyDomain(self):
      pass

   def mainDomain(self):
      pass

   def loadStandbyDomain(self):
      self.standbyCommon()
      self.standbyDomain()

   def loadMainDomain(self):
      self.main = self.newComponent(PowerDomain)
      self.createScd()
      self.createAsics()
      self.mainDomain()

   def createCpu(self):
      logging.error("cpu not declared for this card")

   def loadCpuDomain(self):
      self.createCpu()
      if self.cpu:
         assert self.slot, 'cpu needs to create a slot object'
         self.loadMainDomain()

   def powerStandbyDomainIs(self, on):
      raise NotImplementedError()

   def powerLcpuIs(self, on, lcpuCtx):
      raise NotImplementedError()

   def powerPremainPowerDomainIs(self, on):
      '''Enable Microsemi downstream port and Plx.'''
      assert self.gpio1, "gpio1 is not created yet."
      if on:
         assert self.poweredOn(), "Card is not turned on."
         self.setPlxPcieUpstreamLink(True)
         self.gpio1.pcieReset(False)
         waitFor(self.plx.smbusPing, "Can't take Plx out of reset.")
         self.setupPlx()
      else:
         self.gpio1.pcieReset(True)
         self.setPlxPcieUpstreamLink(False)

   def powerMainPowerDomainIs(self, on):
      if on:
         for asicId, asic in enumerate(self.asics):
            logging.debug('Taking asic %d on card %s out of reset', asicId, self)
            asic.resetIn()
            waitFor(asic.isInReset, "Can't have asic in reset")
            asic.resetOut()
            logging.debug('Asic %d on card %s is out of reset', asicId, self)
      else:
         for asicId, asic in enumerate(self.asics):
            logging.debug('Putting asic %d on card %s in reset', asicId, self)
            asic.resetIn()
            waitFor(asic.isInReset, "Can't have asic in reset")
            logging.debug('Asic %d on card %s is in reset', asicId, self)

      pciRescan() # XXX I believe pci rescan has a pretty big caveat

      if on:
         # Check chip visiblity in pci domain
         for asic in self.asics:
            asic.waitForIt()

   def powerOnIs(self, on, lcpuCtx=None):
      if on:
         self.slot.enablePciPort()
         self.powerStandbyDomainIs(True)
         self.powerPremainPowerDomainIs(True)
         if lcpuCtx:
            self.powerLcpuIs(True, lcpuCtx)
         else:
            self.powerMainPowerDomainIs(True)
      else:
         self.slot.disablePciPort()
         if lcpuCtx:
            self.powerLcpuIs(False, lcpuCtx)
         else:
            self.powerMainPowerDomainIs(False)
         self.powerPremainPowerDomainIs(False)
         self.powerStandbyDomainIs(False)

   def poweredOn(self):
      return self.gpio1.powerGood()

   def powerCycleStandbyDomain(self):
      '''Power cycle standby domain.'''
      assert self.gpio1, "gpio1 is not created yet."
      self.gpio1.powerCycle(True)

   def setPlxPcieUpstreamLink(self, bind):
      if bind:
         return self.slot.parent.pciSwitch.bind(self.slot.slotId)
      else:
         return self.slot.parent.pciSwitch.unbind(self.slot.slotId)

   def enablePlxDownstreamHotplug(self):
      # Enabling hot plug for plx and reset it.
      self.plx.enableHotPlug()
      self.gpio1.pcieReset(True)
      waitFor(lambda: (not self.plx.smbusPing()), "Can't take Plx in reset")
      self.gpio1.pcieReset(False)
      waitFor(self.plx.smbusPing, "Can't take Plx out of reset")

      pciRescan()

   def setupPlx(self):
      self.enablePlxDownstreamHotplug()

class DenaliCardSlot(CardSlot):
   def __init__(self, parent, slotId, pci, bus, presenceGpio=None, card=None):
      super(DenaliCardSlot, self).__init__(parent, slotId)
      self.pci = pci
      self.bus = bus
      self.card = card
      self.presenceGpio = presenceGpio
      if not self.card:
         self.loadCard(DenaliCard(self))

   def getPresence(self):
      if self.presenceGpio is None:
         return self.card.pca.ping()

      return self.presenceGpio.isActive()

   def getEeprom(self):
      if not self.getPresence():
         return None
      self.card.pca.takeOwnership()
      return self.card.eeprom.prefdl()

   def pciAddr(self, domain=0, bus=0, device=0, func=0):
      addr = copy.deepcopy(self.pci)

      addr.domain += domain
      addr.bus += bus
      addr.device += device
      addr.func += func

      return addr
