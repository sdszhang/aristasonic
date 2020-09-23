
from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc
from ...descs.sensor import Position, SensorDesc

from . import PmbusPsu

class DeltaPsu(PsuModel):
   MANUFACTURER = 'delta'
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


class DPS495CB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-495CB A',   'PWR-500AC-F', Airflow.FORWARD),
      PsuIdent('DPS-495CB-1 A', 'PWR-500AC-R', Airflow.REVERSE),
   ]

class DPS750AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-750AB-24 C', 'PWR-745AC-F', Airflow.FORWARD),
      PsuIdent('DPS-750AB-24 A', 'PWR-745AC-F', Airflow.FORWARD),
      PsuIdent('DPS-750AB-25 A', 'PWR-745AC-R', Airflow.REVERSE),
   ]

class DPS1500AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-1500AB-7 A', 'PWR-1511-AC-RED', Airflow.FORWARD),
   ]

class DPS1600CB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-1600CB P', 'PWR-1611-AC-RED', Airflow.FORWARD),
   ]

class DPS1900AB(DeltaPsu):
   DRIVER = 'dps1900'
   IDENTIFIERS = [
      PsuIdent('DPS-1900AB A',   'PWR-1900AC-F', Airflow.FORWARD),
      PsuIdent('DPS-1900AB-1 A', 'PWR-1900AC-R', Airflow.REVERSE),
   ]
