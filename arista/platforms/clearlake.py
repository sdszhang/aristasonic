from ..core.component import Priority
from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.psu import PsuSlot
from ..core.types import PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.trident2 import Trident2
from ..components.dpm import Ucd90120A, UcdGpi
from ..components.max6658 import Max6658
from ..components.psu.delta import DPS495CB
from ..components.psu.artesyn import DS495SPE
from ..components.scd import Scd
from ..components.ds125br import Ds125Br

from ..descs.gpio import GpioDesc
from ..descs.sensor import Position, SensorDesc

from .cpu.crow import CrowCpu

@registerPlatform()
class Clearlake(FixedSystem):

   SID = ['Clearlake', 'ClearlakeSsd']
   SKU = ['DCS-7050QX-32S', 'DCS-7050QX-32S-SSD']

   def __init__(self):
      super(Clearlake, self).__init__()

      self.sfpRange = incrange(1, 4)
      self.qsfp40gAutoRange = incrange(5, 28)
      self.qsfp40gOnlyRange = incrange(29, 36)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.allQsfps)

      self.newComponent(Trident2, PciAddr(bus=0x01))

      scd = self.newComponent(Scd, PciAddr(bus=0x02))

      cpu = self.newComponent(CrowCpu, scd, hwmonBus=1)
      self.cpu = cpu
      self.syscpld = cpu.syscpld

      scd.createWatchdog()

      scd.createPowerCycle()

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c), sensors=[
         SensorDesc(diode=0, name='Board Sensor',
                    position=Position.OTHER, target=36, overheat=55, critical=70),
         SensorDesc(diode=1, name='Front-panel temp sensor',
                    position=Position.INLET, target=42, overheat=65, critical=75),
      ])

      scd.newComponent(Ucd90120A, scd.i2cAddr(1, 0x4e, t=3))
      scd.newComponent(Ucd90120A, scd.i2cAddr(5, 0x4e, t=3), causes={
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'powerloss': UcdGpi(7),
      })
      scd.newComponent(Ds125Br, scd.i2cAddr(6, 0xff), priority=Priority.BACKGROUND)

      scd.addSmbusMasterRange(0x8000, 6)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addReset(ResetGpio(0x4000, 0, False, 'switch_chip_reset'))

      scd.addGpios([
         GpioDesc("psu1_present", 0x5000, 0, ro=True),
         GpioDesc("psu2_present", 0x5000, 1, ro=True),
         GpioDesc("mux", 0x6940, 0), # FIXME: oldSetup order/name
      ])

      for psuId in incrange(1, 2):
         addrFunc=lambda addr, i=psuId: \
                  scd.i2cAddr(2 + i, addr, t=3, datr=3, datw=3)
         name = "psu%d" % psuId
         scd.newComponent(
            PsuSlot,
            slotId=psuId,
            addrFunc=addrFunc,
            presentGpio=scd.inventory.getGpio("%s_present" % name),
            led=scd.inventory.getLed(name),
            psus=[
               DPS495CB,
               DS495SPE,
            ],
         )

      addr = 0x6100
      for xcvrId in self.qsfp40gAutoRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append((addr, name))
            addr += 0x10
         scd.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x6720
      for xcvrId in self.qsfp40gOnlyRange:
         name = "qsfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x30 if xcvrId % 2 else 0x50

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x10

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]

      addr = 0x5010
      bus = 8
      for xcvrId in self.allQsfps:
         intr = intrRegs[1].getInterruptBit(xcvrId - 5)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0x5210
      bus = 40
      for xcvrId in sorted(self.sfpRange):
         scd.addSfp(addr, xcvrId, bus,
                    leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         addr += 0x10
         bus += 1

@registerPlatform()
class ClearlakePlus(Clearlake):
   SID = ['ClearlakePlus', 'ClearlakePlusSsd']
   SKU = ['DCS-7050QX2-32S', 'DCS-7050QX2-32S-SSD']
