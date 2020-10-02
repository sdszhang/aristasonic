
from ...core.platform import registerPlatform
from ...core.register import RegisterMap, Register, RegBitField, SetClearRegister
from ...core.utils import incrange

from ...drivers.scd.register import ScdStatusChangedRegister, ScdSramRegister

from ..cpu.hedgehog import HedgehogCpu

from ...components.eeprom import PrefdlSeeprom
from ...components.lm75 import Tmp75
from ...components.phy.b52 import B52
from ...components.scd import I2cScd
from ...components.tmp464 import Tmp464

from ...descs.sensor import Position, SensorDesc

from .clearwater import ClearwaterBase

class ClearwaterCpuScdRegMap(RegisterMap):
   REVISION = Register(0x01, name='revision')
   SCRATCHPAD = Register(0x02, name='scratchpad', ro=False)
   SLOT_ID = Register(0x03, name='slotId', ro=False)
   STATUS0 = ScdStatusChangedRegister(0x04,
      RegBitField(0, name='lcpuPowerGood'),
      RegBitField(2, name='lcpuInReset'),
      RegBitField(3, name='lcpuMuxSel', flip=True),
   )
   STATUS1 = ScdStatusChangedRegister(0x06,
      RegBitField(6, name='vrmAlert'),
      RegBitField(7, name='vrmHot'),
   )
   STATUS2 = ScdStatusChangedRegister(0x05,
      RegBitField(0, name='lcpuThermTrip'),
      RegBitField(1, name='lcpuHot'),
      RegBitField(2, name='lcpuAlert'),
   )
   STATUS7 = ScdStatusChangedRegister(0x12,
      RegBitField(3, name='lcpuPresent'),
   )
   LCPU_CTRL = SetClearRegister(0x30, 0x31,
      RegBitField(0, name='lcpuDisableSet', ro=False),
      RegBitField(1, name='lcpuResetSet', ro=False),
      RegBitField(3, name='supGmacReset', ro=False),
      RegBitField(4, name='lcpuGmacReset', ro=False),
      RegBitField(5, name='gmacLowPower', ro=False),
   )
   PROVISION = Register(0x32, name='provision', ro=False)
   SRAM = ScdSramRegister(0x33, name='sram')

class ClearwaterCpuBase(ClearwaterBase):
   CPU_CLS = HedgehogCpu
   STANDBY_TEMP_SENSORS_CLS = Tmp75

   def mainDomain(self):
      super(ClearwaterCpuBase, self).mainDomain()

      self.scd.newComponent(Tmp464, self.scd.i2cAddr(8, 0x48), sensors=[
         SensorDesc(diode=0, name='Center back', position=Position.OTHER,
                    target=75, overheat=85, critical=95),
         SensorDesc(diode=1, name='Fap0 core0', position=Position.OTHER,
                    target=85, overheat=100, critical=105),
         SensorDesc(diode=2, name='Fap0 core1', position=Position.OTHER,
                    target=85, overheat=100, critical=105),
         SensorDesc(diode=3, name='PCIE', position=Position.OTHER,
                    target=75, overheat=85, critical=90),
      ])

      # Riser cards prefdl
      for riserId in incrange(1, 12):
         bus = 96 + riserId
         self.scd.newComponent(PrefdlSeeprom, self.scd.i2cAddr(bus, 0x50))

   def standbyDomain(self):
      super(ClearwaterCpuBase, self).standbyDomain()
      self.syscpld = self.pca.newComponent(I2cScd, addr=self.slot.bus.i2cAddr(0x23),
                                           registerCls=ClearwaterCpuScdRegMap)

@registerPlatform()
class Clearwater2(ClearwaterCpuBase):
   SID = ['Clearwater2']
   SKU = ['7800R3-48CQ2-LC', '7800R-48QC2-LC']
   PLX_LCPU_MODE = [
      # VS0 (sup)
      ((1 << 0) |  # sup1
       (1 << 2) |  # sup2
       (1 << 13)), # gmac
      # VS1 (lcpu)
      ((1 << 1) |  # lcpu
       (1 << 3) |  # j2
       (1 << 5))   # scd
   ]

@registerPlatform()
class Clearwater2Ms(Clearwater2):
   SID = ['Clearwater2Ms']
   SKU = ['7800R3-48CQM2-LC', '7800R-48QCM2-LC']

   PHY_CLS = B52
