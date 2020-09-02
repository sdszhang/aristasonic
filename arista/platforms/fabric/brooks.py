from ...core.platform import registerPlatform

from ...components.tmp464 import Tmp464

from ...descs.sensor import SensorDesc, Position

from .dragonfly import Dragonfly

@registerPlatform()
class Brooks(Dragonfly):
   SID = ['Brooks']
   SKU = ['DCS-7804-FM']

   def createStandbySensors(self):
      self.pca.newComponent(Tmp464, self.slot.bus.i2cAddr(0x48), sensors=[
         SensorDesc(diode=0, name='Board sensor 1',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=1, name='Ramon 0 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=2, name='Ramon 1 PCB',
                    position=Position.OTHER, target=70, overheat=80, critical=90),
         SensorDesc(diode=3, name='Outlet',
                    position=Position.OUTLET, target=75, overheat=85, critical=95),
         SensorDesc(diode=4, name='Inlet',
                    position=Position.INLET, target=75, overheat=85, critical=95),
      ])
      self.pca.newComponent(Tmp464, self.slot.bus.i2cAddr(0x49), sensors=[
         SensorDesc(diode=0, name='Board sensor 2',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=2, name='Ramon 0 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
         SensorDesc(diode=3, name='Ramon 1 Core (secondary)',
                    position=Position.OTHER, target=75, overheat=85, critical=95),
      ])
