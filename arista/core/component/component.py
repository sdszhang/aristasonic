
from . import Component as LegacyComponent
from . import Priority

class Component(LegacyComponent):

   DRIVER = None
   PRIORITY = Priority.DEFAULT
   REGISTER_CLS = None

   def __init__(self, *args, **kwargs):
      # HACK: some refactor is required to get rid of this
      #       the addr is not always provided as a kwarg
      if args and 'addr' not in kwargs:
         kwargs['addr'] = args[0]
         args = args[1:]
      kwargs.setdefault('registerCls', self.REGISTER_CLS)
      drivers = [
         self.DRIVER(**kwargs), # pylint: disable=not-callable
      ]
      # TODO: cleanup the parent dependency when possible
      super(Component, self).__init__(
         *args,
         drivers=drivers,
         priority=self.PRIORITY,
         **kwargs
      )
      assert len(self.drivers) == 1, "New style components can only have one driver"
      self.driver = next(iter(self.drivers.values()))
      self.addObjects(**kwargs)

   def addObjects(self, fans=None, leds=None, sensors=None, **kwargs):
      for sensor in sensors or []:
         self.addTempSensor(sensor)
      for fan in fans or []:
         self.addFan(fan)
      for led in leds or []:
         self.addLed(led)

   def addFan(self, desc, **kwargs):
      return self.inventory.addFan(self.driver.getFan(desc, **kwargs))

   def addFans(self, descs, **kwargs):
      return [self.addFan(desc, **kwargs) for desc in descs]

   def addFanLed(self, desc, **kwargs):
      return self.inventory.addLed(self.driver.getFanLed(desc, **kwargs))

   def addFanLeds(self, descs, **kwargs):
      return [self.addFanLed(desc, **kwargs) for desc in descs]

   def addLed(self, desc, **kwargs):
      return self.inventory.addLed(self.driver.getLed(desc, **kwargs))

   def addLeds(self, descs, **kwargs):
      return [self.addLed(desc, **kwargs) for desc in descs]

   def addTempSensor(self, desc, **kwargs):
      return self.inventory.addTemp(self.driver.getTempSensor(desc, **kwargs))

   def addTempSensors(self, descs, **kwargs):
      return [self.addTempSensor(desc, **kwargs) for desc in descs]

   def addReset(self, desc, **kwargs):
      return self.inventory.addReset(self.driver.getReset(desc, **kwargs))

   def addResets(self, descs, **kwargs):
      return [self.addReset(desc, **kwargs) for desc in descs]

   def addGpio(self, desc, **kwargs):
      return self.inventory.addGpio(self.driver.getGpio(desc, **kwargs))

   def addGpios(self, descs, **kwargs):
      return [self.addGpio(desc, **kwargs) for desc in descs]
