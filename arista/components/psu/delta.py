
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
      PsuIdent('DPS-495CB C',   'PWR-500AC-F', Airflow.FORWARD),
      PsuIdent('DPS-495CB-1 C', 'PWR-500AC-R', Airflow.REVERSE),
   ]

class DPS500AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-500AB-40 A', 'PWR-511-AC-RED', Airflow.FORWARD),
      PsuIdent('DPS-500AB-41 A', 'PWR-511-DC-RED', Airflow.FORWARD),
      PsuIdent('DPS-500AB-42 A', 'PWR-511-DC-BLUE', Airflow.REVERSE),
      PsuIdent('DPS-500AB-43 A', 'PWR-511-AC-BLUE', Airflow.REVERSE),
   ]

class DPS750AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-750AB-24 A', 'PWR-745AC-F', Airflow.FORWARD),
      PsuIdent('DPS-750AB-24 B', 'PWR-745AC-F', Airflow.FORWARD),
      PsuIdent('DPS-750AB-24 C', 'PWR-745AC-F', Airflow.FORWARD),
      PsuIdent('DPS-750AB-25 A', 'PWR-745AC-R', Airflow.REVERSE),
      PsuIdent('DPS-750AB-25 B', 'PWR-745AC-R', Airflow.REVERSE),
      PsuIdent('DPS-750AB-25 C', 'PWR-745AC-R', Airflow.REVERSE),
   ]

class DPS1500AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-1500AB-7 A', 'PWR-1511-AC-RED', Airflow.FORWARD),
      PsuIdent('DPS-1500AB-9 A', 'PWR-1511-DC-RED', Airflow.FORWARD),
   ]

class DPS1600AB(DeltaPsu):
   IDENTIFIERS = [
      PsuIdent('DPS-1600AB-14 A', 'PWR-1611-DC-RED', Airflow.FORWARD),
   ]

   DESCRIPTION = PsuDesc(
      sensors=[
         SensorDesc(diode=0,
                    name='Power supply %(psuId)d hotspot sensor',
                    position=Position.OTHER,
                    target=86, overheat=92, critical=98),
         SensorDesc(diode=1,
                    name='Power supply %(psuId)d inlet temp sensor',
                    position=Position.INLET,
                    target=52, overheat=60, critical=65),
         SensorDesc(diode=2,
                    name='Power supply %(psuId)d exhaust temp sensor',
                    position=Position.OUTLET,
                    target=86, overheat=92, critical=98),
      ]
   )

class DPS1600CB(DPS1600AB):
   IDENTIFIERS = [
      PsuIdent('DPS-1600CB P', 'PWR-1611-AC-RED', Airflow.FORWARD),
      PsuIdent('DPS-1600CB N', 'PWR-1600AC-F', Airflow.FORWARD),
   ]

class DPS1900AB(DeltaPsu):
   DRIVER = 'dps1900'
   IDENTIFIERS = [
      PsuIdent('DPS-1900AB A',   'PWR-1900AC-F', Airflow.FORWARD),
      PsuIdent('DPS-1900AB-1 A', 'PWR-1900AC-R', Airflow.REVERSE),
   ]

class ECD16020102(DeltaPsu):
   DRIVER = 'dps800'
   IDENTIFIERS = [
      PsuIdent('ECD16020102', 'PWR-3001-AC-RED', Airflow.FORWARD),
   ]

class ECD26020037(DeltaPsu):
   DRIVER = 'dps800'
   IDENTIFIERS = [
      PsuIdent('ECD26020037', 'PWR-3001-DC-RED', Airflow.FORWARD),
   ]

class ECD16020097(DeltaPsu):
   PMBUS_ADDR = 0x40
   DRIVER = 'dps800'
   IDENTIFIERS = [
      PsuIdent('ECD16020097', 'PWR-D1-3041-AC-BLUE', Airflow.REVERSE),
   ]
