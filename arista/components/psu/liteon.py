from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc
from ...descs.sensor import Position, SensorDesc

from . import PmbusPsu

class LiteonPsu(PsuModel):
   MANUFACTURER = 'liteon power'
   PMBUS_ADDR = 0x58

   PMBUS_CLS = PmbusPsu
   DESCRIPTION = PsuDesc(
      sensors=[
         SensorDesc(diode=0,
                    name='Power supply %(psuId)d inlet temp sensor',
                    position=Position.INLET,
                    target=60, overheat=75, critical=85),
         SensorDesc(diode=1,
                    name='Power supply %(psuId)d secondary hotspot sensor',
                    position=Position.OTHER,
                    target=70, overheat=105, critical=110),
         SensorDesc(diode=2,
                    name='Power supply %(psuId)d primary hotspot sensor',
                    position=Position.OTHER,
                    target=70, overheat=95, critical=100),
      ]
   )

class PS2102(LiteonPsu):
   DRIVER = 'dps800'
   IDENTIFIERS = [
      PsuIdent('PS-2102-1A ', 'PWR-1011-AC-RED',  Airflow.FORWARD),
      PsuIdent('DD-2102-1A ', 'PWR-1011-DC-RED',  Airflow.FORWARD),
      PsuIdent('PS-2102-1AR', 'PWR-1011-AC-BLUE', Airflow.REVERSE),
      PsuIdent('DD-2102-1AR', 'PWR-1011-DC-BLUE', Airflow.REVERSE),
   ]
