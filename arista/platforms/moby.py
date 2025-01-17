
from ..core.fixed import FixedSystem, FixedChassis
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.psu import PsuSlot
from ..core.xcvr import EthernetImpl, EthernetSlotImpl, XcvrSlot
from ..core.utils import incrange

from ..components.asic.xgs.tomahawk5 import Tomahawk5
from ..components.cpld import SysCpldReloadCauseRegistersV2, SysCpldCause
from ..components.max6581 import Max6581
from ..components.minke import Minke
from ..components.scd import Scd
from ..components.lm75 import Tmp75
from ..components.xcvr import CmisEeprom

from ..descs.reset import ResetDesc
from ..descs.sensor import Position, SensorDesc
from ..descs.xcvr import Osfp800, Qsfp28, Xcvr as XcvrDesc

from .cpu.redstart import RedstartCpu

class BackplaneImpl(EthernetImpl):
   def __init__(self, eeprom, slot):
      super().__init__(slot)
      self.addr = eeprom.addr

   def getType(self):
      return 'backplane'

class PaladinConnector(XcvrSlot):
   def __init__(self, *args, eeprom=None, **kwargs):
      super().__init__(*args, **kwargs)
      self.slotInv = self.inventory.addEthernetSlot(EthernetSlotImpl(self))
      self.xcvrInv = self.inventory.addEthernet(BackplaneImpl(eeprom, self.slotInv))
      self.xcvr = eeprom
      self.leds = []

   def getPresence(self):
      # TODO: use presencGpio in the future
      return True

class PaladinHd(XcvrDesc):
   LANES = 48
   SPEED = 100

class MobyChassis(FixedChassis):
   FAN_SLOTS = 3
   FAN_COUNT = 2
   HEIGHT_RU = 1

   @classmethod
   def addFanboard(cls, parent, bus):
      return Minke(parent, bus)

@registerPlatform()
class Moby(FixedSystem):

   CHASSIS = MobyChassis
   CPU_CLS = RedstartCpu
   LED_FP_TRICOLOR = True

   BACKPLANE_CONNECTORS = 8
   BACKPLANE_CARTRIDGES = 4

   PORTS = PortLayout(
      (Osfp800(i) for i in incrange(1, 16)),
      (PaladinHd(i) for i in range(17, 17 + BACKPLANE_CONNECTORS)),
      (Qsfp28(25),),
   )

   SID = ['Moby', 'Redstart8CFixedNMoby']
   SKU = ['DCS-7060X6-16PE-384C']

   def __init__(self):
      super().__init__()

      self.cpu = self.newComponent(self.CPU_CLS)
      self.syscpld = self.cpu.syscpld

      port = self.cpu.getPciPort(2)
      scd = port.newComponent(Scd, addr=port.addr)
      self.scd = scd

      scd.addSmbusMasterRange(0x8000, 2, 0x80, 6)
      scd.setMsiRearmOffset(0x180)
      scd.createWatchdog()

      scd.addResets([
         ResetDesc('switch_chip_pcie_reset', addr=0x4000, bit=3, auto=False),
         ResetDesc('switch_chip_reset', addr=0x4000, bit=2, auto=False),
      ])

      scd.newComponent(Max6581, addr=scd.i2cAddr(0, 0x4d), sensors=[
         SensorDesc(diode=0, name='Switch Card temp sensor',
                    position=Position.OTHER, target=85, overheat=95, critical=105),
         SensorDesc(diode=1, name='TH5 PCB Left',
                    position=Position.OTHER, target=105, overheat=115, critical=125),
         SensorDesc(diode=2, name='TH5 PCB Right',
                    position=Position.OTHER, target=105, overheat=115, critical=125),
         SensorDesc(diode=3, name='Inlet Ambiant Air',
                    position=Position.OTHER, target=85, overheat=95, critical=105),
         SensorDesc(diode=6, name='TH5 Diode 1',
                    position=Position.OTHER, target=105, overheat=115, critical=125),
         SensorDesc(diode=7, name='TH5 Diode 2',
                    position=Position.OTHER, target=105, overheat=115, critical=125),
      ])

      scd.addLeds([
         (0x6010 + 0x4 * i, f'blade{i+1}') for i in range(0, 12)
      ])
      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu_status'),
      ])

      self.cartridge_eeproms = [
         scd.newComponent(
            CmisEeprom,
            addr=scd.i2cAddr(12 + i, 0x50),
            portName=f'cartridge{i}',
         ) for i in range(0, self.BACKPLANE_CARTRIDGES)
      ]

      # Make the backplane connector appear as individual port for proper
      # integration with xcvrd
      self.backplane = [
         scd.newComponent(
            PaladinConnector,
            name=f'back{i}',
            slotId=17 + i,
            eeprom=self.cartridge_eeproms[-(1 + i // 2)],
         ) for i in range(0, self.BACKPLANE_CONNECTORS)
      ]

      for psuId, bus in [(1, 16), (2, 17)]:
         addrFunc=lambda addr, bus=bus: \
                  scd.i2cAddr(bus, addr, t=3, datr=2, datw=3)
         self.scd.newComponent(
            PsuSlot,
            slotId=psuId,
            addrFunc=addrFunc,
            presentGpio=True,
         )

      port = self.cpu.getPciPort(3)
      pscd = port.newComponent(Scd, addr=port.addr)
      self.pscd = pscd

      pscd.addSmbusMasterRange(0x8000, 18, 0x80, 1)

      pscd.newComponent(Tmp75, addr=pscd.i2cAddr(0, 0x4a), sensors=[
         SensorDesc(diode=0, name='Port Card', position=Position.OTHER,
            target=65, overheat=80, critical=95),
      ])

      pintrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]
      pscd.addXcvrSlots(
         ports=self.PORTS.getOsfps(),
         addr=0xA000,
         bus=2,
         ledAddr=0x6104,
         ledAddrOffsetFn=lambda x: 0x10,
         intrRegs=pintrRegs,
         intrRegIdxFn=lambda _: 1,
         intrBitFn=lambda xcvrId: xcvrId - 1,
      )
      pscd.addXcvrSlots(
         ports=self.PORTS.getQsfps(),
         addr=0xA100,
         bus=17,
         ledAddr=0x6200,
         ledAddrOffsetFn=lambda x: 0x10,
         intrRegs=pintrRegs,
         intrRegIdxFn=lambda _: 1,
         intrBitFn=lambda xcvrId: xcvrId - 1,
      )

      port = self.cpu.getPciPort(0)
      port.newComponent(Tomahawk5, addr=port.addr,
         coreResets=[
            scd.inventory.getReset('switch_chip_reset'),
         ],
         pcieResets=[
            scd.inventory.getReset('switch_chip_pcie_reset'),
         ],
      )

      self.syscpld.addReloadCauseProvider(causes=[
         SysCpldCause(0x00, SysCpldCause.UNKNOWN),
         SysCpldCause(0x01, SysCpldCause.OVERTEMP),
         SysCpldCause(0x02, SysCpldCause.SEU),
         SysCpldCause(0x03, SysCpldCause.WATCHDOG,
                      priority=SysCpldCause.Priority.HIGH),
         SysCpldCause(0x04, SysCpldCause.CPU, 'CPU source or CPU PGOOD',
                      priority=SysCpldCause.Priority.LOW),
         SysCpldCause(0x08, SysCpldCause.REBOOT),
         SysCpldCause(0x0a, SysCpldCause.POWERLOSS, 'PSU DC'),
         SysCpldCause(0x0f, SysCpldCause.SEU, 'bitshadow rx parity error'),
      ], regmap=SysCpldReloadCauseRegistersV2)
