
from __future__ import absolute_import, division, print_function

import copy

from ...core.card import Card, CardSlot
from ...core.fabric import Fabric
from ...core.linecard import Linecard
from ...core.log import getLogger
from ...core.types import PciAddr
from ...descs.led import LedColor
from ...libs.pci import readSecondaryBus
from ...libs.wait import waitFor

from ..dpm.ucd import Ucd90320
from ..eeprom import At24C512
from ..pca9541 import Pca9541
from ..power import PowerDomain

logging = getLogger(__name__)

class DenaliCard(Card):
   # Connect supes 1 and 2 via Plx upstream ports 0 and 2
   PCIE_SWITCH_UPSTREAM_PORTS = {
      1: 0,
      2: 2,
   }

   ASIC_PLX_DOWNSTREAM_PORTS = {}

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

   def getUpstreamPort(self):
      return self.PCIE_SWITCH_UPSTREAM_PORTS[self.slot.parent.getSlotId()]

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
      self.pca = self.standby.newComponent(Pca9541, addr=self.slot.bus.i2cAddr(0x77),
                                           driverMode='user')
      self.eeprom = self.pca.newComponent(At24C512, addr=self.pca.i2cAddr(0x50),
                                          label='card_%d' % self.slot.slotId)
      self.standbyUcd = self.pca.newComponent(Ucd90320, addr=self.pca.i2cAddr(0x11))
      self.createGpio1()
      if self.gpio1 is not None:
         self.gpio1.addRedGreenGpioLed('status', 'statusRed', 'statusGreen')
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
         self.gpio1.pcieReset(False)
         waitFor(self.plx.smbusPing, "Can't take Plx out of reset.")
         self.setupPlx()
         self.enablePlxPcieUpstreamLink(True)
         self.getInventory().getLed('status').setColor(LedColor.AMBER)
      else:
         self.enablePlxPcieUpstreamLink(False)
         self.gpio1.pcieReset(True)
         self.getInventory().getLed('status').setColor(LedColor.OFF)

   def getAsicPciAddr(self, asicId, asic):
      plxDownstreamAddr = PciAddr(bus=self.plxDownstreamBus,
                                  device=self.ASIC_PLX_DOWNSTREAM_PORTS[asicId])
      asicUpstreamBus = readSecondaryBus(plxDownstreamAddr)
      return PciAddr(bus=asicUpstreamBus)

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

      if on:
         self.slot.enablePciPort()
         # PLX is up. We now can get PLX downtream bus to asics, and
         # achieve asics' PCI addr.
         self.updateAsicAddr()
         # Verify asic presence
         for asicId, asic in enumerate(self.asics):
            self.asics[asicId].waitForIt()

   def powerOnIs(self, on, lcpuCtx=None):
      if on:
         # Make sure the port is disabled before we start. If it isn't we risk
         # triggering bogus PCI state that will result in kernel lockups later.
         self.slot.disablePciPort()
         self.powerStandbyDomainIs(True)
         self.powerPremainPowerDomainIs(True)
         if lcpuCtx:
            self.powerLcpuIs(True, lcpuCtx)
         else:
            self.powerMainPowerDomainIs(True)
         self.slot.enablePciPort()
      else:
         self.slot.disablePciPort()
         if lcpuCtx:
            self.powerLcpuIs(False, lcpuCtx)
         else:
            self.powerMainPowerDomainIs(False)
         self.powerPremainPowerDomainIs(False)
         self.powerStandbyDomainIs(False)

   def poweredOn(self):
      if self.runningOnLcpu():
         return True
      if self.gpio1 is None:
         # Linecard is likely unsupported or not loaded
         return False
      try:
         return self.gpio1.powerGood()
      except Exception: # broad-except
         logging.debug('%s: failed to read power good', self)
         return False

   def enablePlxPcieUpstreamLink(self, bind):
      self.plx.disableUpstreamPort(self.getUpstreamPort(), True)
      if bind:
         self.slot.parent.pciSwitch.bind(self.slot.slotId)
         self.plx.disableUpstreamPort(self.getUpstreamPort(), False)
      else:
         self.slot.parent.pciSwitch.unbind(self.slot.slotId)

   def setupPlx(self):
      self.plx.enableHotPlug()
      self.plx.setUpstreamPort(self.getUpstreamPort())
      self.plx.enableNt(False)

   def setupIdentification(self):
      self.pca.takeOwnership()
      self.pca.setup()
      self.eeprom.setup()

   def updateAsicAddr(self):
      self.plxDownstreamBus = readSecondaryBus(self.slot.pci)
      for asicId, asic in enumerate(self.asics):
         self.asics[asicId].addr = self.getAsicPciAddr(asicId, asic)

class DenaliCardSlot(CardSlot):

   CARD_CLS = None

   def __init__(self, parent, slotId, pci, bus, presenceGpio=None, card=None):
      super(DenaliCardSlot, self).__init__(parent, slotId)
      self.pci = pci
      self.bus = bus
      self.card = card
      self.presenceGpio = presenceGpio
      if not self.card:
         self.loadCard(self.CARD_CLS(self))

   def getPresence(self):
      if self.presenceGpio is None:
         return self.card.pca.ping()

      return self.presenceGpio.isActive()

   def getEeprom(self):
      if not self.getPresence():
         return None
      self.card.setupIdentification()
      return self.card.eeprom.prefdl()

   def pciAddr(self, domain=0, bus=0, device=0, func=0):
      addr = copy.deepcopy(self.pci)

      addr.domain += domain
      addr.bus += bus
      addr.device += device
      addr.func += func

      return addr

class DenaliLinecardBase(DenaliCard, Linecard):
   pass

class DenaliFabricBase(DenaliCard, Fabric):
   pass

class DenaliLinecardSlot(DenaliCardSlot):
   CARD_CLS = DenaliLinecardBase

class DenaliFabricSlot(DenaliCardSlot):
   CARD_CLS = DenaliFabricBase
