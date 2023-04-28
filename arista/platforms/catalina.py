from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.psu import PsuSlot
from ..core.utils import incrange

from ..components.asic.xgs.tomahawk4 import Tomahawk4
from ..components.dpm.ucd import Ucd90320, UcdGpi
from ..components.lm73 import Lm73
from ..components.tmp464 import Tmp464
from ..components.phy.babbagelp import BabbageLP
from ..components.psu.liteon import PS2242
from ..components.scd import Scd

from ..descs.gpio import GpioDesc
from ..descs.reset import ResetDesc
from ..descs.sensor import Position, SensorDesc
from ..descs.xcvr import Osfp, QsfpDD, Sfp

from .chassis.tuba import Tuba

from .cpu.lorikeet import LorikeetCpu

@registerPlatform()
class CatalinaP(FixedSystem):

   SID = ['CatalinaP']
   SKU = ['DCS-7060PX5-64S']

   CHASSIS = Tuba

   PHY = BabbageLP

   PORTS = PortLayout(
      (Osfp(i) for i in incrange(1, 64)),
      (Sfp(i) for i in incrange(65, 66)),
   )

   def __init__(self):
      super(CatalinaP, self).__init__()

      self.cpu = self.newComponent(LorikeetCpu)
      self.cpu.addCpuDpm()
      self.cpu.cpld.newComponent(Ucd90320, addr=self.cpu.switchDpmAddr(0x11),
                                 causes={
         'overtemp': UcdGpi(1),
         'powerloss': UcdGpi(3),
         'psufault': UcdGpi(4),
         'watchdog': UcdGpi(5),
         'cpu': UcdGpi(6),
         'reboot': UcdGpi(8),
      })
      # TODO sys cpld
      #self.syscpld = self.cpu.syscpld

      port = self.cpu.getPciPort(0)
      scd = port.newComponent(Scd, addr=port.addr)
      self.scd = scd

      scd.createWatchdog()

      scd.newComponent(Tmp464, addr=scd.i2cAddr(8, 0x48), sensors=[
         SensorDesc(diode=0, name='Switch card',
                    position=Position.OTHER, target=85, overheat=95, critical=105),
         SensorDesc(diode=1, name='Air outlet',
                    position=Position.OUTLET, target=85, overheat=95, critical=105),
         SensorDesc(diode=2, name='Air inlet',
                    position=Position.INLET, target=85, overheat=95, critical=105),
      ])

      scd.newComponent(Lm73, addr=self.scd.i2cAddr(13, 0x48), sensors=[
         SensorDesc(diode=0, name='Front-panel temp sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
      ])

      scd.addSmbusMasterRange(0x8000, 11, 0x80)

      scd.addResets([
         ResetDesc('phy3_reset', addr=0x4000, bit=7),
         ResetDesc('phy2_reset', addr=0x4000, bit=6),
         ResetDesc('phy1_reset', addr=0x4000, bit=5),
         ResetDesc('phy0_reset', addr=0x4000, bit=4),
         ResetDesc('switch_chip_pcie_reset', addr=0x4000, bit=3, auto=False),
         ResetDesc('switch_chip_reset', addr=0x4000, bit=2, auto=False),
      ])

      scd.addGpios([
         GpioDesc("psu1_present", 0x5000, 0, ro=True),
         GpioDesc("psu2_present", 0x5000, 1, ro=True),
         GpioDesc("psu1_status", 0x5000, 8, ro=True),
         GpioDesc("psu2_status", 0x5000, 9, ro=True),
         GpioDesc("psu1_ac_status", 0x5000, 10, ro=True),
         GpioDesc("psu2_ac_status", 0x5000, 11, ro=True),
      ])

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
         scd.createInterrupt(addr=0x3090, num=3),
      ]

      scd.addXcvrSlots(
         ports=self.PORTS.getOsfps(),
         addr=0xA000,
         bus=24,
         ledAddr=0x6100,
         ledAddrOffsetFn=lambda x: 0x10,
         intrRegs=intrRegs,
         intrRegIdxFn=lambda xcvrId: xcvrId // 33 + 1,
         intrBitFn=lambda xcvrId: (xcvrId - 1) % 32,
      )

      scd.addXcvrSlots(
         ports=self.PORTS.getSfps(),
         addr=0xA900,
         bus=88,
         ledAddr=0x6900,
         ledAddrOffsetFn=lambda x: 0x40,
      )

      # PSU
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
            led=self.cpu.cpld.inventory.getLed("%s" % name),
            psus=[
               PS2242,
            ],
         )

      scd.addMdioMasterRange(0x9000, 4)

      for i in range(0, 4):
         phyId = i + 1
         reset = scd.inventory.getReset('phy%d_reset' % (i // 2))
         mdios = [scd.addMdio(i, 0), scd.addMdio(i, 1)]
         phy = self.PHY(phyId, mdios, reset=reset)
         self.inventory.addPhy(phy)

      port = self.cpu.getPciPort(1)
      port.newComponent(Tomahawk4, addr=port.addr,
         coreResets=[
            scd.inventory.getReset('switch_chip_reset'),
         ],
         pcieResets=[
            scd.inventory.getReset('switch_chip_pcie_reset'),
         ],
      )

@registerPlatform()
class CatalinaDD(CatalinaP):
   SID = ['CatalinaDD']
   SKU = ['DCS-7060DX5-64S']

   PORTS = PortLayout(
      (QsfpDD(i) for i in incrange(1, 64)),
      (Sfp(i) for i in incrange(65, 66)),
   )
