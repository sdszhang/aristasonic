from ..core.fixed import FixedChassis, FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.psu import PsuSlot
from ..core.types import PciAddr
from ..core.utils import incrange

from ..components.asic.xgs.trident3 import Trident3
from ..components.dpm.ucd import Ucd9090A, UcdGpi
from ..components.phy.broncos import Broncos
from ..components.psu.fixed import Fixed150AC
from ..components.scd import Scd
from ..components.tmp464 import Tmp464

from ..descs.gpio import GpioDesc
from ..descs.reset import ResetDesc
from ..descs.sensor import Position, SensorDesc

from .cpu.newport import NewportCpu

class NewportChassis(FixedChassis):
    FAN_SLOTS = 1
    FAN_COUNT = 2
    HEIGHT_RU = 1

@registerPlatform()
class Newport(FixedSystem):

   SID = ['Newport']
   SKU = ['DCS-7010TX-48']

   CHASSIS = NewportChassis

   PHY = Broncos

   PORTS = PortLayout(
      ethernets=incrange(1, 48),
      sfps=incrange(49, 52),
   )

   def __init__(self):
      super().__init__()

      self.cpu = self.newComponent(NewportCpu)

      scd = self.newComponent(Scd, PciAddr(device=0x18, func=5))
      self.scd = scd

      scd.newComponent(Tmp464, scd.i2cAddr(8, 0x48), sensors=[
         SensorDesc(diode=0, name='Board temp sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
         SensorDesc(diode=1, name='Front air temp sensor',
                    position=Position.INLET, target=50, overheat=63, critical=73),
         SensorDesc(diode=2, name='Rear air temp sensor',
                    position=Position.OUTLET, target=50, overheat=63, critical=73),
      ])

      scd.createWatchdog()
      scd.createPowerCycle()
      scd.addFanGroup(0x2000, 0, self.CHASSIS.FAN_SLOTS, self.CHASSIS.FAN_COUNT)
      scd.addFanSlotBlock(
         slotCount=self.CHASSIS.FAN_SLOTS,
         fanCount=self.CHASSIS.FAN_COUNT,
         statusLed=(0x0550, 'fan_status')
      )

      scd.addSmbusMasterRange(0x8000, 0, 0x80, bus=9)

      scd.addLeds([
         (0x0510, 'status'),
         (0x0520, 'psu1'),
         (0x0530, 'psu2'),
         (0x0540, 'beacon'),
      ])

      scd.newComponent(Ucd9090A, scd.i2cAddr(3, 0x75), causes={
         'overtemp': UcdGpi(5),
         'reboot': UcdGpi(7),
         'watchdog': UcdGpi(8),
         'powerloss': UcdGpi(10),
      })

      scd.addResets([
         ResetDesc('phy2_reset', addr=0x0170, bit=5),
         ResetDesc('phy1_reset', addr=0x0170, bit=4),
         ResetDesc('phy0_reset', addr=0x0170, bit=3),
         ResetDesc('switch_chip_reset', addr=0x0170, bit=0),
         ResetDesc('switch_chip_pcie_reset', addr=0x0170, bit=1)
      ])

      scd.addGpios([
         GpioDesc("psu1_status", 0x0310, 1, ro=True),
         GpioDesc("psu2_status", 0x0310, 0, ro=True),
      ])

      for psuId in incrange(1, 2):
         name = "psu%d" % psuId
         scd.newComponent(
            PsuSlot,
            slotId=psuId,
            presentGpio=True, # Always present
            inputOkGpio=scd.inventory.getGpio("%s_status" % name),
            outputOkGpio=scd.inventory.getGpio("%s_status" % name),
            led=scd.inventory.getLed(name),
            forcePsuLoad=True,
            psus=[
               # Note: No SMBus access to PSU
               Fixed150AC,
            ],
         )

      # TODO: Newport fans: one fan-tray with two fans

      intr = scd.createInterrupt(addr=0x0200, num=0)
      scd.createWatchdog(intr=intr, bit=4)

      # TODO: Add support for Ethernet ports
      scd.addEthernetSlotBlock(
         ethernetRange=self.PORTS.ethernetRange,
         ledAddr=0x6000,
      )

      scd.addSfpSlotBlock(
         sfpRange=self.PORTS.sfpRange,
         addr=0x0800,
         bus=4,
         ledAddr=0x0700,
         intrRegs=[intr],
         intrRegIdxFn=lambda xcvrId: 0,
         intrBitFn=lambda xcvrId: 5 + xcvrId - 49
      )

      scd.addMdioMaster(0x9000, 0)
      for i in range(0, 3):
         phyId = i + 1
         reset = scd.inventory.getReset('phy%d_reset' % i)
         mdios = [scd.addMdio(0, i * 9)]
         phy = self.PHY(phyId, mdios, reset=reset)
         self.inventory.addPhy(phy)
