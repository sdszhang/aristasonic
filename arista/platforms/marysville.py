from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.psu import PsuSlot
from ..core.types import PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.trident3 import Trident3
from ..components.dpm import Ucd90160, Ucd90320, UcdGpi
from ..components.psu.delta import DPS500AB
from ..components.scd import Scd
from ..components.tmp464 import Tmp464

from ..descs.gpio import GpioDesc
from ..descs.sensor import Position, SensorDesc

from .cpu.woodpecker import WoodpeckerCpu

@registerPlatform()
class Marysville(FixedSystem):

   SID = ['Marysville']
   SKU = ['DCS-7050SX3-48YC8']

   def __init__(self):
      super(Marysville, self).__init__()

      self.sfpRange = incrange(1, 48)
      self.qsfp100gRange = incrange(49, 52)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.qsfp100gRange)

      self.newComponent(Trident3, addr=PciAddr(bus=0x01))

      scd = self.newComponent(Scd, addr=PciAddr(bus=0x02))

      self.cpu = self.newComponent(WoodpeckerCpu)
      self.cpu.cpld.newComponent(Ucd90160, addr=self.cpu.cpuDpmAddr())
      self.cpu.cpld.newComponent(Ucd90320, addr=self.cpu.switchDpmAddr(), causes={
         'powerloss': UcdGpi(4),
         'reboot': UcdGpi(5),
         'watchdog': UcdGpi(6),
         'overtemp': UcdGpi(7),
      })

      scd.createWatchdog()

      scd.newComponent(Tmp464, addr=scd.i2cAddr(2, 0x48), sensors=[
         SensorDesc(diode=0, name='Switch Card temp sensor', position=Position.OTHER,
                    target=85, overheat=100, critical=110),
         SensorDesc(diode=1, name='Front-panel temp sensor', position=Position.INLET,
                    target=60, overheat=65, critical=75),
         SensorDesc(diode=2, name='Front PCB temp sensor', position=Position.OTHER,
                    target=70, overheat=75, critical=80),
      ])

      scd.addSmbusMasterRange(0x8000, 7, 0x80)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addResets([
         ResetGpio(0x4000, 1, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_pcie_reset'),
      ])

      scd.addGpios([
         GpioDesc("psu1_present", 0x5000, 0, ro=True),
         GpioDesc("psu2_present", 0x5000, 1, ro=True),
         GpioDesc("psu1_status", 0x5000, 8, ro=True),
         GpioDesc("psu2_status", 0x5000, 9, ro=True),
         GpioDesc("psu1_ac_status", 0x5000, 10, ro=True),
         GpioDesc("psu2_ac_status", 0x5000, 11, ro=True),
      ])

      for psuId in incrange(1, 2):
         addrFunc = lambda addr, i=psuId: \
               scd.i2cAddr(-1 + i, addr, t=3, datr=3, datw=3)
         name = "psu%d" % psuId
         scd.newComponent(
            PsuSlot,
            slotId=psuId,
            addrFunc=addrFunc,
            presentGpio=scd.inventory.getGpio("%s_present" % name),
            inputOkGpio=scd.inventory.getGpio("%s_ac_status" % name),
            outputOkGpio=scd.inventory.getGpio("%s_status" % name),
            led=scd.inventory.getLed('%s' % name),
            psus=[
               DPS500AB,
            ],
         )

      addr = 0x6100
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x10

      addr = 0x6400
      for xcvrId in self.qsfp100gRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append((addr, name))
            addr += 0x10
         scd.addLedGroup("qsfp%d" % xcvrId, leds)

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xa000
      bus = 8
      for xcvrId in self.sfpRange:
         name = 'sfp%d' % xcvrId
         intr = intrRegs[xcvrId // 33 + 1].getInterruptBit(name, (xcvrId - 1) % 32)
         scd.addSfp(addr, xcvrId, bus, interruptLine=intr,
                    leds=scd.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0xa300
      bus = 56
      for xcvrId in self.qsfp100gRange:
         name = 'qsfp%d' % xcvrId
         intr = intrRegs[2].getInterruptBit(name, xcvrId - 33)
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=scd.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

@registerPlatform()
class Marysville10(Marysville):
   SID = ['Marysville10']
   SKU = ['DCS-7050SX3-48C8']
