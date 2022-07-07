
from ...core.platform import registerPlatform
from ...core.port import PortLayout
from ...core.utils import incrange

from ...components.asic.dnx.jericho2c import Jericho2cPlus
from ...components.denali.desc import DenaliAsicDesc
from ...components.denali.linecard import (
   DenaliLinecard,
   GpioRegisterMap,
   StandbyScdRegisterMap,
)
from ...components.eeprom import At24C512
from ...components.pca9555 import Pca9555
from ...components.plx import PlxPortDesc
from ...components.scd import I2cScd
from ...components.tmp464 import Tmp464

from ...descs.sensor import Position, SensorDesc

from ..cpu.hedgehog import HedgehogCpu

class WolverineStandbyRegMap(StandbyScdRegisterMap):
   pass

class Wolverine(DenaliLinecard):
   CPU_CLS = HedgehogCpu
   ASICS = [
      DenaliAsicDesc(cls=Jericho2cPlus, asicId=0),
      DenaliAsicDesc(cls=Jericho2cPlus, asicId=1),
   ]
   XCVR_BUS_OFFSET = 24
   PLX_PORTS = [
      PlxPortDesc(port=0, name='sup1', upstream=True),
      PlxPortDesc(port=1, name='lcpu', vs=PlxPortDesc.VS1, upstream=True),
      PlxPortDesc(port=2, name='sup2', upstream=True),
      PlxPortDesc(port=3, name='je0', vs=PlxPortDesc.VS1),
      PlxPortDesc(port=4, name='je1', vs=PlxPortDesc.VS1),
      PlxPortDesc(port=5, name='scd', vs=PlxPortDesc.VS1),
      PlxPortDesc(port=13, name='gmac'),
   ]

   PORTS = PortLayout(
      osfps=incrange(1, 36),
   )

   def createPorts(self):
      intrRegs = [self.scd.getInterrupt(intId) for intId in incrange(0, 6)]
      # IRQ2 -> port 32:1 (bit 31:0)
      # IRQ3 -> port 36:33 (bit 3:0)
      self.scd.addOsfpSlotBlock(
         osfpRange=self.PORTS.osfpRange,
         addr=0xA010,
         bus=self.XCVR_BUS_OFFSET,
         ledAddr=0x6100,
         intrRegs=intrRegs,
         intrRegIdxFn=lambda xcvrId: xcvrId // 32 + 2,
         intrBitFn=lambda xcvrId: (xcvrId - 1) % 32,
         isHwModSelAvail=False,
      )

      for riserId in incrange(1, 18):
         bus = 64 + riserId - 1
         self.scd.newComponent(At24C512, addr=self.scd.i2cAddr(bus, 0x50),
                               label='card%d_riser%s' % (self.slot.slotId, riserId))

   def mainDomain(self):
      self.scd.addSmbusMasterRange(0x8000, 10, spacing=0x80)

      for intId in incrange(0, 6):
         addr = 0x3000 + intId * 0x30
         self.scd.createInterrupt(addr=addr, num=intId)

      # At the moment there is no unique name for objects added to the kernel such
      # as leds, mdios, ... As a result, the kernel does some renaming, which is
      # not handled by the platform library. Until we have support for something
      # like slot prefixes for kernel objects, we only create the ports in LCPU
      # mode.
      if self.cpu:
         self.createPorts()
         self.cpu.addSmbusComponents(self.scd)

   def createGpio1(self):
      self.gpio1 = self.pca.newComponent(Pca9555, addr=self.pca.i2cAddr(0x74),
                                         registerCls=GpioRegisterMap)

   def standbyDomain(self):
      self.syscpld = self.pca.newComponent(I2cScd, addr=self.pca.i2cAddr(0x23),
                                           registerCls=WolverineStandbyRegMap)

      self.pca.newComponent(Tmp464, addr=self.pca.i2cAddr(0x48),
                            sensors=[
         SensorDesc(diode=0, name='Right', position=Position.OTHER,
                    target=70, overheat=80, critical=90),
         SensorDesc(diode=1, name='Inlet', position=Position.INLET,
                    target=70, overheat=100, critical=105),
         SensorDesc(diode=2, name='Outlet', position=Position.OUTLET,
                    target=70, overheat=100, critical=105),
         SensorDesc(diode=3, name='Fap0 Back', position=Position.OUTLET,
                    target=75, overheat=90, critical=100),
         SensorDesc(diode=4, name='Fap1 Back', position=Position.OUTLET,
                    target=75, overheat=90, critical=100),
      ])
      self.pca.newComponent(Tmp464, addr=self.pca.i2cAddr(0x49),
                            sensors=[
         SensorDesc(diode=0, name='Fap0 Front', position=Position.OTHER,
                    target=70, overheat=80, critical=90),
         SensorDesc(diode=1, name='Fap0 C', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=2, name='Fap0 AVS', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=3, name='Fap0 FAB', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=4, name='Fap0 NIF', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
      ])
      self.pca.newComponent(Tmp464, addr=self.pca.i2cAddr(0x4a),
                            sensors=[
         SensorDesc(diode=0, name='Fap1 Front', position=Position.OTHER,
                    target=70, overheat=80, critical=90),
         SensorDesc(diode=1, name='Fap1 C', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=2, name='Fap1 AVS', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=3, name='Fap1 FAB', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
         SensorDesc(diode=4, name='Fap1 NIF', position=Position.OTHER,
                    target=75, overheat=100, critical=105),
      ])

@registerPlatform()
class WolverineO(Wolverine):
   SID = ['WolverineO']
   SKU = ['7800R3A-36P-LC']

@registerPlatform()
class WolverineOBk(Wolverine):
   SID = ['WolverineOBk']
   SKU = ['7800R3AK-36P-LC']

@registerPlatform()
class WolverineOMs(Wolverine):
   SID = ['WolverineOMs']
   SKU = ['7800R3A-36PM-LC']

@registerPlatform()
class WolverineOBkMs(Wolverine):
   SID = ['WolverineOBkMs']
   SKU = ['7800R3AK-36PM-LC']

@registerPlatform()
class WolverineQ(Wolverine):
   SID = ['WolverineQ']
   SKU = ['7800R3A-36D-LC']

@registerPlatform()
class WolverineQBk(Wolverine):
   SID = ['WolverineQBk']
   SKU = ['7800R3AK-36D-LC']

@registerPlatform()
class WolverineQMs(Wolverine):
   SID = ['WolverineQMs']
   SKU = ['7800R3A-36DM-LC']

@registerPlatform()
class WolverineQBkMs(Wolverine):
   SID = ['WolverineQBkMs']
   SKU = ['7800R3AK-36DM-LC']

@registerPlatform()
class WolverineQCpu(Wolverine):
   SID = ['WolverineQCpu']
   SKU = ['7800R3A-36D2-LC']

@registerPlatform()
class WolverineQCpuBk(Wolverine):
   SID = ['WolverineQCpuBk']
   SKU = ['7800R3AK-36D2-LC']

@registerPlatform()
class WolverineQCpuMs(Wolverine):
   SID = ['WolverineQCpuMs']
   SKU = ['7800R3A-36DM2-LC']

@registerPlatform()
class WolverineQCpuBkMs(Wolverine):
   SID = ['WolverineQCpuBkMs']
   SKU = ['7800R3AK-36DM2-LC']
