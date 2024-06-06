from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from . import PmbusPsu
from .helper import psuDescHelper, Position

class AristaPsu(PsuModel):
   MANUFACTURER = 'arista'
   PMBUS_ADDR = 0x58
   PMBUS_CLS = PmbusPsu

class Pwr568(AristaPsu):
   CAPACITY = 2000
   DESCRIPTION = psuDescHelper(
      sensors=[
         ('inlet', Position.OTHER, 60, 65, 70),
         ('secondary hotspot', Position.OTHER, 110, 120, 130),
         ('primary hotspot', Position.OTHER, 110, 115, 120),
      ],
   )
   IDENTIFIERS = [
      PsuIdent('PWR-00568', 'PWR-2011-AC-RED', Airflow.EXHAUST),
   ]


class Pwr591(AristaPsu):
   CAPACITY = 2400
   DESCRIPTION = psuDescHelper(
      sensors=[
         ('inlet', Position.OTHER, 60, 65, 70),
         ('secondary hotspot', Position.OTHER, 110, 120, 130),
         ('primary hotspot', Position.OTHER, 110, 115, 120),
      ],
   )
   IDENTIFIERS = [
      PsuIdent('PWR-00591', 'PWR-2411-MC-RED', Airflow.EXHAUST),
   ]

class Pwr663(AristaPsu):
   CAPACITY = 2400
   DESCRIPTION = psuDescHelper(
      sensors=[
         ('inlet', Position.OTHER, 60, 65, 70),
         ('secondary hotspot', Position.OTHER, 110, 120, 130),
         ('primary hotspot', Position.OTHER, 110, 115, 120),
      ],
   )
   IDENTIFIERS = [
      PsuIdent('PWR-00663', 'PWR-2422-HV-RED', Airflow.EXHAUST),
   ]
