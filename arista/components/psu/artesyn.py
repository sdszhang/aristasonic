from ...core.cooling import Airflow
from ...core.psu import PsuModel, PsuIdent

from ...descs.psu import PsuDesc
from ...descs.sensor import Position, SensorDesc

from . import PmbusPsu
from .ds460 import Ds460

class ArtesynPsu(PsuModel):
   MANUFACTURER = 'artesyn'
   MANUFACTURER_ALIASES = ['emerson'] # NOTE: acquired by Emerson
   PMBUS_ADDR = 0x58

class DS495SPE(ArtesynPsu):
   CAPACITY = 500
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

class DS460(ArtesynPsu):
   CAPACITY = 460
   IDENTIFIERS = [
      # NOTE: that first entry is a workaround for insufficient information exposed
      # through the pmbus MFR_*. Proper identification would require IPMI eeprom
      # parsing.
      PsuIdent('DS460', 'PWR-460AC-F', Airflow.FORWARD),

      PsuIdent('DS460S-3    ', 'PWR-460AC-F', Airflow.FORWARD),
      PsuIdent('DS460S-3-001', 'PWR-460AC-R', Airflow.REVERSE),
      PsuIdent('DS460S-3-002', 'PWR-460AC-F', Airflow.FORWARD),
      PsuIdent('DS460S-3-003', 'PWR-460AC-R', Airflow.REVERSE),
   ]

   PMBUS_CLS = Ds460
   DESCRIPTION = PsuDesc(
      sensors=[
         SensorDesc(diode=0, name='Power supply %(psuId)d inlet temp sensor',
                    position=Position.INLET,
                    target=39, overheat=60, critical=70),
         SensorDesc(diode=1, name='Power supply %(psuId)d internal sensor',
                    position=Position.OTHER,
                    target=55, overheat=80, critical=150),
      ]
   )

class CSU500DP(DS495SPE):
   CAPACITY = 500
   IDENTIFIERS = [
      PsuIdent('CSU500DP-3    ', 'PWR-511-AC-RED', Airflow.FORWARD),
      PsuIdent('CSU500DP-3-001', 'PWR-511-AC-BLUE', Airflow.REVERSE),
   ]
