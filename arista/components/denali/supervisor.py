
from __future__ import absolute_import, division, print_function

from ...core.card import LC_BASE_SLOTID, FC_BASE_SLOTID
from ...core.supervisor import Supervisor
from ...core.types import PciAddr

from .card import DenaliCardSlot

from ...descs.gpio import GpioDesc

from ..eeprom import PrefdlSeeprom
from ..microsemi import Microsemi, MicrosemiPort
from ..scd import Scd

class DenaliSupervisor(Supervisor):
   LINECARD_PORTS = []
   FABRIC_PORTS = []

   def __init__(self, scdAddr=None, pciSwitchCls=Microsemi, **kwargs):
      super(DenaliSupervisor, self).__init__(**kwargs)

      self.chassisEeproms = []

      self.pciSwitch = None
      self.pciSwitchCls = pciSwitchCls

      self.linecardCount = len(self.LINECARD_PORTS)
      self.fabricCount = len(self.FABRIC_PORTS)

      self.linecardSmbus = range(0, self.linecardCount)
      self.fabricSmbus = range(self.linecardCount,
                               self.linecardCount + self.fabricCount)

      self.scd = None
      self.scdAddr = scdAddr

      self.createScd()
      self.createPciSwitch()
      self.createLinecards()
      self.createFabricCards()

   def createScd(self):
      self.scd = self.newComponent(Scd, self.scdAddr)
      self.scd.addSmbusMasterRange(0x8000, 3, 0x80)
      self.scd.addUartPortRange(0x7e00, self.linecardCount)

      self.scd.createWatchdog()

      self.scd.addGpios([
         GpioDesc("supervisor_want_active", 0x5000, 0),
         GpioDesc("supervisor_active", 0x5000, 1, ro=True),
         GpioDesc("supervisor_slotid", 0x5000, 2, ro=True),
         GpioDesc("peer_supervisor_present", 0x5000, 3, ro=True),
         GpioDesc("heartbeat_in", 0x5000, 4, ro=True),
         GpioDesc("heartbeat_out", 0x5000, 5),
      ])

      self.chassisEeproms = [
         self.scd.newComponent(PrefdlSeeprom, addr=self.scd.i2cAddr(14, 0x51),
                               name='chassis1'),
         self.scd.newComponent(PrefdlSeeprom, addr=self.scd.i2cAddr(15, 0x51),
                               name='chassis2'),
      ]

   def createPciSwitch(self):
      ports = {}

      for idx, portDesc in enumerate(self.LINECARD_PORTS):
         portAddr = PciAddr(bus=0x06, device=0x7 + idx)
         cardAddr = PciAddr(bus=0x46 + 0xb * idx)
         ports[LC_BASE_SLOTID + idx] = MicrosemiPort(portDesc, addr=portAddr,
                                                     upstreamAddr=cardAddr)

      for idx, portDesc in enumerate(self.FABRIC_PORTS):
         portAddr = PciAddr(bus=0x06, device=idx)
         cardAddr = PciAddr(bus=0x07 + 0xa * idx)
         ports[FC_BASE_SLOTID + idx] = MicrosemiPort(portDesc, addr=portAddr,
                                                     upstreamAddr=cardAddr)

      self.pciSwitch = self.newComponent(self.pciSwitchCls,
                                         # XXX: confirm that this is true for all
                                         # Denali.
                                         addr=PciAddr(bus=0x05, device=0x00, func=1),
                                         ports=ports)

   def createLinecards(self):
      for lcId in range(self.linecardCount):
         name = "lc%d" % (lcId + 1)
         slotId = lcId + LC_BASE_SLOTID
         self.scd.addGpios([
            GpioDesc("%s_present" % name, 0x4100, lcId, ro=True),
            GpioDesc("%s_present_changed" % name, 0x4100, 16 + lcId),
         ])
         bus = self.scd.getSmbus(self.linecardSmbus[lcId])
         pci = PciAddr(bus=0x47 + 0xb * lcId)
         presenceGpio = self.inventory.getGpio("%s_present" % name)
         self.linecardSlots.append(DenaliCardSlot(self, slotId, pci, bus,
                                                  presenceGpio=presenceGpio))

   def createFabricCards(self):
      self.fabricSmbus = range(8, 8 + 6)
      self.fabricSlots = []

      for fcId in range(self.fabricCount):
         name = "fc%d" % (fcId + 1)
         slotId = fcId + FC_BASE_SLOTID
         self.scd.addGpios([
            GpioDesc("%s_present" % name, 0x4110, fcId, ro=True),
            GpioDesc("%s_present_changed" % name, 0x4110, 16 + fcId),
         ])
         bus = self.scd.getSmbus(self.fabricSmbus[fcId])
         pci = PciAddr(bus=0x07 + 0xa * fcId)
         presenceGpio = self.inventory.getGpio("%s_present" % name)
         self.fabricSlots.append(DenaliCardSlot(self, slotId, pci, bus,
                                                presenceGpio=presenceGpio))

   def readSlotId(self):
      # FIXME: read the slotId via scd gpio
      return 0
