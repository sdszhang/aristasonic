from ...core.cpu import Cpu
from ...core.pci import PciRoot

from ...components.cpu.amd.k10temp import K10Temp
from ...components.cpld import SysCpld, SysCpldCommonRegistersV2
from ...components.dpm.adm1266 import Adm1266, AdmPin, AdmPriority
from ...components.max6658 import Max6658
from ...components.scd import Scd

from ...descs.sensor import Position, SensorDesc

class Puffin(Cpu):

   PLATFORM = 'puffin'

   def __init__(self, cpldRegisterCls=SysCpldCommonRegistersV2, **kwargs):
      super().__init__(**kwargs)

      self.pciRoot = self.newComponent(PciRoot)

      port = self.pciRoot.rootPort(device=0x18, func=3)
      port.newComponent(K10Temp, addr=port.addr, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=70, overheat=95, critical=115),
      ])

      port = self.pciRoot.rootPort(device=0x18, func=7)
      cpld = port.newComponent(Scd, addr=port.addr)
      self.cpld = cpld

      cpld.createInterrupt(addr=0x3000, num=0)

      cpld.addLeds([
         (0x4000, 'beacon'),
         (0x4010, 'status'),
         (0x4020, 'fan_status'),
         (0x4030, 'psu1'),
         (0x4040, 'psu2'),
      ])

      cpld.createPowerCycle()
      cpld.addSmbusMasterRange(0x8000, 1, 0x80, 4)

      cpld.newComponent(Max6658, addr=cpld.i2cAddr(0, 0x4c), sensors=[
         SensorDesc(diode=0, name='Cpu board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=85),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=55, overheat=75, critical=85),
      ])

      self.addCpuDpm()

      self.addFanGroup(self.parent.CHASSIS.FAN_SLOTS, self.parent.CHASSIS.FAN_COUNT)

      self.syscpld = self.newComponent(SysCpld, addr=cpld.i2cAddr(4, 0x23),
                                       registerCls=cpldRegisterCls)
      self.syscpld.addPowerCycle()

   def addCpuDpm(self, addr=None, causes=None):
      addr = addr or self.cpuDpmAddr()
      return self.cpld.newComponent(Adm1266, addr=addr, causes=causes or {
         # TODO
      })

   def cpuDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(5, addr, t=t, **kwargs)

   def switchGpAddr(self, addr, **kwargs):
      return self.cpld.i2cAddr(4, addr, **kwargs)

   def getScdPciPort(self):
      bridge = self.pciRoot.pciBridge(device=0x01, func=2)
      return bridge.downstreamPort(port=0)

   def getAsicPciPort(self, index=0):
      if index == 0:
         bridge = self.pciRoot.pciBridge(device=0x01, func=1)
         return bridge.downstreamPort(port=0)
      return None

   def addFanGroup(self, slots=3, count=2):
      self.cpld.addFanGroup(0x9000, 3, slots, count)
      self.cpld.addFanSlotBlock(slotCount=slots, fanCount=count)
