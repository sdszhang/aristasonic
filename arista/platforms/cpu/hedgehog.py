from ...core.component.i2c import Component
from ...core.cpu import Cpu
from ...core.pci import PciRoot
from ...core.register import Register, RegisterMap
from ...core.types import PciAddr
from ...core.utils import getCmdlineDict

from ...components.cpu.amd.k10temp import K10Temp
from ...components.rpc import LinecardRpcClient
from ...components.scd import Scd
from ...components.watchdog import FakeWatchdog

from ...descs.led import LedDesc, LedColor
from ...descs.sensor import SensorDesc, Position

class FakeI2cBus(Component):
  def i2cAddr(self, *args):
      return None

class HedgehogCpuCpld(RegisterMap):
   REVISION = Register(0x10, name='revision')
   SCRATCHPAD = Register(0x20, name='scratchpad', ro=False)
   SLOT_ID = Register(0x30, name='slotId')
   PROVISION = Register(0x50, name='provision')

class HedgehogCpu(Cpu):

   PLATFORM = 'hedgehog'

   def __init__(self, **kwargs):
      super(HedgehogCpu, self).__init__(**kwargs)
      self.slot = None
      self.pciRoot = self.newComponent(PciRoot)

      port = self.pciRoot.rootPort(device=0x18, func=7)
      self.syscpld = port.newComponent(Scd, addr=port.addr,
                                       registerCls=HedgehogCpuCpld)

      port = self.pciRoot.rootPort(device=0x18, func=3)
      port.newComponent(K10Temp, addr=port.addr, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=60, overheat=90, critical=95),
      ])

      self.inventory.addWatchdog(FakeWatchdog())

      self.rpc = self.newComponent(LinecardRpcClient)
      self.rpc.addLed(
         LedDesc('status', colors=[LedColor.RED, LedColor.GREEN, LedColor.OFF]))

   def getSlotId(self):
      # NOTE: this slotId value is used by Plx to deduce the lcpu upstreamPort
      return 0

   def createCardSlot(self, cls, card):
      slotId = int(getCmdlineDict().get('slot_id', 0))
      pci = self.pciRoot.rootPort(device=0x03, func=1)
      bus = FakeI2cBus()
      self.slot = cls(self, slotId, pci, bus, card=card)
      return self.slot
