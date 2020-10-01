from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc
from ...descs.sensor import Position, SensorDesc

from . import PmbusPsu

class ArtesynPsu(PsuModel):
   MANUFACTURER = 'artesyn' # NOTE: acquired by Emerson
   PMBUS_ADDR = 0x58

class DS495SPE(ArtesynPsu):
   IDENTIFIERS = [
      PsuIdent('DS495SPE-3-401 ', 'PWR-500AC-F', Airflow.FORWARD),
      PsuIdent('DS495SPE-3-402 ', 'PWR-500AC-R', Airflow.REVERSE),
   ]

   PMBUS_CLS = PmbusPsu
   DESCRIPTION = PsuDesc(
      sensors=[
         SensorDesc(diode=0,
                    name='Power supply %(psuId)d hotspot sensor',
                    position=Position.OTHER,
                    target=80, overheat=95, critical=100),
         SensorDesc(diode=1,
                    name='Power supply %(psuId)d inlet temp sensor',
                    position=Position.INLET,
                    target=55, overheat=70, critical=75),
         SensorDesc(diode=2,
                    name='Power supply %(psuId)d exhaust temp sensor',
                    position=Position.OUTLET,
                    target=80, overheat=108, critical=113),
      ]
   )
