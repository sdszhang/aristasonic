from ...core.cpu import Cpu
from ...core.pci import PciRoot

from ...components.cpu.amd.k10temp import K10Temp
from ...components.cpu.lorikeet import (
    LorikeetCpldRegisters,
    LorikeetSysCpld,
)
from ...components.dpm.adm1266 import Adm1266, AdmPin, AdmPriority
from ...components.max6658 import Max6658
from ...components.scd import Scd

from ...descs.sensor import Position, SensorDesc

class LorikeetCpu(Cpu):

   PLATFORM = 'lorikeet'

   def __init__(self, cpldRegisterCls=LorikeetCpldRegisters, **kwargs):
      super(LorikeetCpu, self).__init__(**kwargs)

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
      cpld.addSmbusMasterRange(0x8000, 2, 0x80, 4)

      cpld.newComponent(Max6658, addr=cpld.i2cAddr(0, 0x4c), sensors=[
         SensorDesc(diode=0, name='CPU board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=85),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=55, overheat=75, critical=85),
      ])

      self.addFanGroup(self.parent.CHASSIS.FAN_SLOTS, self.parent.CHASSIS.FAN_COUNT)

      cpld.addFanSlotBlock(
         slotCount=self.parent.CHASSIS.FAN_SLOTS,
         fanCount=self.parent.CHASSIS.FAN_COUNT,
      )

      self.syscpld = self.newComponent(LorikeetSysCpld, addr=cpld.i2cAddr(4, 0x23),
                                       registerCls=cpldRegisterCls)

      # TODO: Add ISL69247 temp sensors

   def addCpuDpm(self, addr=None, causes=None):
      addr = addr or self.cpuDpmAddr()
      return self.cpld.newComponent(Adm1266, addr=addr, causes=causes or {
         'fansmissing': AdmPin(5, AdmPin.GPIO),
         'overtemp': AdmPin(6, AdmPin.GPIO),
         'procerror': AdmPin(7, AdmPin.GPIO, priority=AdmPriority.LOW),
      })

   def cpuDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x4f, t=3, **kwargs):
      return self.cpld.i2cAddr(5, addr, t=t, **kwargs)

   def addFanGroup(self, slots=3, count=2):
      self.cpld.addFanGroup(0x9000, 3, slots, count)

   def getPciPort(self, num):
      device, func = {
         0: (0x01, 1),
         1: (0x03, 1),
      }[num]
      bridge = self.pciRoot.pciBridge(device=device, func=func)
      return bridge.downstreamPort(port=0)
