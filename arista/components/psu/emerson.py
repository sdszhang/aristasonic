from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc
from ...descs.sensor import Position, SensorDesc

from . import PmbusPsu

class EmersonPsu(PsuModel):
   MANUFACTURER = 'emerson'
   PMBUS_ADDR = 0x58

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

class DS750PED(EmersonPsu):
   IDENTIFIERS = [
      PsuIdent('DS750PED-3', 'PWR-745AC-F', Airflow.FORWARD),
   ]

class CSU500DP3(EmersonPsu):
   IDENTIFIERS = [
      PsuIdent('CSU500DP-3', 'PWR-511-AC-RED', Airflow.FORWARD),
      PsuIdent('CSU500DP-3-001', 'PWR-511-AC-BLUE', Airflow.REVERSE),
   ]
