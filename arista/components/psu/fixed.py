from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc

class FixedPsuModel(PsuModel):
   MANUFACTURER = 'arista'
   DESCRIPTION = PsuDesc()

class Fixed150AC(FixedPsuModel):
   CAPACITY = 150
   IDENTIFIERS = [
      # Note: Used for Newport
      PsuIdent('PWR-440-AC', 'PWR-440-AC', Airflow.EXHAUST),
   ]
