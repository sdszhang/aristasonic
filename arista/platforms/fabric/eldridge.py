from ...core.platform import registerPlatform
from ...core.register import RegBitField, RegisterMap
from ...core.utils import incrange, HwApi

from ...components.asic.dnx.ramon import Ramon
from ...components.denali.fabric import DenaliFabric
from ...components.dpm import Ucd90320
from ...components.max31790 import Max31790
from ...components.max6658 import Max6658
from ...components.pca9555 import Pca9555
from ...components.tmp464 import Tmp464
from ...components.tmp468 import Tmp468

from ...descs.fan import FanDesc
from ...descs.sensor import SensorDesc, Position

from ...drivers.pca9555 import GpioRegister

class Gpio2Registers(RegisterMap):
   A = GpioRegister(0x0,
      RegBitField(0, 'fanFault1', ro=False),
      RegBitField(1, 'fanFault2', ro=False),
      RegBitField(2, 'fanFault3', ro=False),
      RegBitField(3, 'fanFault4', ro=False),
      RegBitField(4, 'fanFault5', ro=False),
      RegBitField(5, 'fanFault6', ro=False),
      RegBitField(6, 'fanFault7', ro=False),
      RegBitField(7, 'fanFault8', ro=False),
   )
   B = GpioRegister(0x1,
      RegBitField(0, 'ramon0SysReset', flip=True, ro=False),
      RegBitField(1, 'ramon0PcieReset', flip=True, ro=False),
      RegBitField(2, 'ramon1SysReset', flip=True, ro=False),
      RegBitField(3, 'ramon1PcieReset', flip=True, ro=False),
      RegBitField(4, 'ramon2SysReset', flip=True, ro=False),
      RegBitField(5, 'ramon2PcieReset', flip=True, ro=False),
      RegBitField(6, 'ramonSmbusEnable', flip=True, ro=False),
      RegBitField(7, 'polSmbusEnable', flip=True, ro=False),
   )

@registerPlatform()
class Eldridge(DenaliFabric):
   SID = ['Eldridge']
   SKU = ['DCS-7808-FM']

   ASIC_BUSES = [
      0x02,
      0x04,
      0x05,
   ]

   def createGpio2(self):
      if not hasattr(self, 'gpio2') or not self.gpio2:
         self.gpio2 = self.main.newComponent(Pca9555, self.slot.bus.i2cAddr(0x21),
                                             registerCls=Gpio2Registers)
         # FIXME: IO should not happen in the constructor. Move this to setup.
         # Always enable 2 pins to access Ramon and Pol via Smbus
         self.gpio2.ramonSmbusEnable(True)
         self.gpio2.polSmbusEnable(True)

   def createAsics(self):
      asicAddrs = [self.slot.pciAddr(bus=bus) for bus in self.ASIC_BUSES]

      self.createGpio2()
      asicResetGpios = {
         0 : (self.gpio2.ramon0SysReset, self.gpio2.ramon0PcieReset),
         1 : (self.gpio2.ramon1SysReset, self.gpio2.ramon1PcieReset),
         2 : (self.gpio2.ramon2SysReset, self.gpio2.ramon2PcieReset),
      }

      self.asics = []
      for i, addr in enumerate(asicAddrs):
         self.asics.append(self.main.newComponent(
                           Ramon, addr,
                           resetGpio=asicResetGpios[i][0],
                           pcieResetGpio=asicResetGpios[i][1]))

   def standbyDomain(self):
      self.pca.newComponent(Ucd90320, self.slot.bus.i2cAddr(0x11))
      self.pca.newComponent(Max31790, self.slot.bus.i2cAddr(0x2c), fans=[
         FanDesc(fanId=fanId) for fanId in incrange(5, 8)
      ])
      self.pca.newComponent(Max31790, self.slot.bus.i2cAddr(0x2d), fans=[
         FanDesc(fanId=fanId) for fanId in incrange(1, 4)
      ])

      self.createStandbySensors()

   def createOldStandbySensors(self):
      self.pca.newComponent(Tmp468, self.slot.bus.i2cAddr(0x48), sensors=[
         SensorDesc(diode=0, name='Board sensor 1',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=1, name='Ramon 0 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=2, name='Ramon 1 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=3, name='Ramon 2 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=4, name='Inlet',
                    position=Position.INLET, target=75, overheat=85, critical=95),
         SensorDesc(diode=5, name='Exhaust',
                    position=Position.OUTLET, target=75, overheat=85, critical=95),
         SensorDesc(diode=7, name='Ramon 0 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=8, name='Ramon 1 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
      ])
      self.pca.newComponent(Max6658, self.slot.bus.i2cAddr(0x4c), sensors=[
         SensorDesc(diode=0, name='Ramon 2 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
      ])

   def createStandbySensors(self):
      if self.getHwApi() < HwApi(42):
         self.createOldStandbySensors()
         return

      self.pca.newComponent(Tmp464, self.slot.bus.i2cAddr(0x48), sensors=[
         SensorDesc(diode=0, name='Board sensor 1',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=1, name='Ramon 0 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=2, name='Ramon 1 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=3, name='Ramon 2 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=4, name='Inlet',
                    position=Position.INLET, target=75, overheat=85, critical=95),
      ])
      self.pca.newComponent(Tmp464, self.slot.bus.i2cAddr(0x49), sensors=[
         SensorDesc(diode=0, name='Board sensor 2',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=1, name='Exhaust',
                    position=Position.OUTLET, target=75, overheat=85, critical=95),
         SensorDesc(diode=2, name='Ramon 0 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=3, name='Ramon 1 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=4, name='Ramon 2 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
      ])
