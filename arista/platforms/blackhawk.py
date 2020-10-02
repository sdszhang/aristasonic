from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.psu import PsuSlot
from ..core.types import PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.tomahawk3 import Tomahawk3
from ..components.cpu.rook import TehamaFanCpldComponent
from ..components.dpm import Ucd90320, UcdGpi
from ..components.max6581 import Max6581
from ..components.psu.delta import DPS1600AB, DPS1600CB
from ..components.scd import Scd

from ..descs.gpio import GpioDesc
from ..descs.sensor import Position, SensorDesc

from .cpu.rook import RookCpu

@registerPlatform()
class BlackhawkO(FixedSystem):

   SID = ['BlackhawkO']
   SKU = ['DCS-7060PX4-32']

   def __init__(self):
      super(BlackhawkO, self).__init__()

      self.osfpRange = incrange(1, 32)
      self.sfpRange = incrange(33, 34)

      self.inventory.addPorts(osfps=self.osfpRange, sfps=self.sfpRange)

      self.newComponent(Tomahawk3, PciAddr(bus=0x06))

      scd = self.newComponent(Scd, PciAddr(bus=0x07))
      self.scd = scd

      scd.createWatchdog()

      scd.newComponent(Max6581, addr=scd.i2cAddr(8, 0x4d),
                       waitFile='/sys/class/hwmon/hwmon2', sensors=[
         SensorDesc(diode=0, name='Board sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
         SensorDesc(diode=1, name='Switch board middle sensor',
                    position=Position.OTHER, target=55, overheat=65, critical=75),
         SensorDesc(diode=2, name='Switch board left sensor',
                    position=Position.OTHER, target=55, overheat=65, critical=75),
         SensorDesc(diode=3, name='Front-panel temp sensor',
                    position=Position.INLET, target=55, overheat=65, critical=75),
         SensorDesc(diode=6, name='Switch chip diode 1 sensor',
                    position=Position.OTHER, target=75, overheat=110, critical=125),
         SensorDesc(diode=7, name='Switch chip diode 2 sensor',
                    position=Position.OTHER, target=75, overheat=110, critical=125),
      ])

      scd.addSmbusMasterRange(0x8000, 8, 0x80)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addResets([
         ResetGpio(0x4000, 4, False, 'sat_cpld1_reset'),
         ResetGpio(0x4000, 3, False, 'sat_cpld0_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 0, False, 'security_asic_reset'),
      ])

      scd.addGpios([
         GpioDesc("psu2_present", 0x5000, 0, ro=True),
         GpioDesc("psu1_present", 0x5000, 1, ro=True),
         GpioDesc("psu2_status", 0x5000, 8, ro=True),
         GpioDesc("psu1_status", 0x5000, 9, ro=True),
         GpioDesc("psu2_ac_status", 0x5000, 10, ro=True),
         GpioDesc("psu1_ac_status", 0x5000, 11, ro=True),
      ])

      addr = 0x6100
      for xcvrId in self.osfpRange:
         name = "osfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x40

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x40

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 16
      for xcvrId in sorted(self.osfpRange):
         intr = intrRegs[1].getInterruptBit(xcvrId - 1)
         name = 'osfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addOsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0xA210
      bus = 48
      for xcvrId in sorted(self.sfpRange):
         scd.addSfp(addr, xcvrId, bus,
                    leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         addr += 0x10
         bus += 1

      cpu = self.newComponent(RookCpu, fanCount=5, mgmtBus=14,
                              fanCpldCls=TehamaFanCpldComponent)
      cpu.cpld.newComponent(Ucd90320, cpu.switchDpmAddr(0x11), causes={
         'overtemp': UcdGpi(1),
         'powerloss': UcdGpi(3),
         'watchdog': UcdGpi(5),
         'reboot': UcdGpi(6),
      })
      self.cpu = cpu
      self.syscpld = cpu.syscpld

      for psuId, bus in [(1, 12), (2, 11)]:
         addrFunc=lambda addr, bus=bus: \
                  scd.i2cAddr(bus, addr, t=3, datr=2, datw=3)
         name = "psu%d" % psuId
         scd.newComponent(
            PsuSlot,
            slotId=psuId,
            addrFunc=addrFunc,
            presentGpio=scd.inventory.getGpio("%s_present" % name),
            inputOkGpio=scd.inventory.getGpio("%s_ac_status" % name),
            outputOkGpio=scd.inventory.getGpio("%s_status" % name),
            led=cpu.leds.inventory.getLed('%s_status' % name),
            psus=[
               DPS1600CB,
               DPS1600AB,
            ],
         )

@registerPlatform()
class BlackhawkDD(BlackhawkO):
   SID = ['BlackhawkDD']
   SKU = ['DCS-7060DX4-32']
