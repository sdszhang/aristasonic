
from ...descs.fan import FanDesc, FanPosition
from ...descs.psu import PsuDesc
from ...descs.rail import RailDesc, RailDirection
from ...descs.sensor import Position, SensorDesc

def psuDescHelper(hasFans=True, maxRpm=None, minRpm=None,
                  inputRailId=1, inputMaxVoltage=None, inputMinVoltage=None,
                  sensors=None):
   fans = [
      FanDesc(
         fanId=1,
         name='psu%(psuId)d/%(fanId)d',
         position=FanPosition.OUTLET,
         maxRpm=maxRpm,
         minRpm=minRpm
      )
   ] if hasFans else []

   rails=[
      RailDesc(
         railId=inputRailId,
         direction=RailDirection.INPUT,
         maxVoltage=inputMaxVoltage,
         minVoltage=inputMinVoltage,
      )
   ] if inputRailId is not None else []

   sensors = sensors or []
   sensors=[
      SensorDesc(
         diode=i,
         name='Power supply %%(psuId)d %s sensor' % name,
         position=position,
         target=target,
         overheat=overheat,
         critical=critical,
      )
      for i, (name, position, target, overheat, critical) in enumerate(sensors)
   ]

   return PsuDesc(fans=fans, rails=rails, sensors=sensors)
