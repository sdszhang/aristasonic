from collections import OrderedDict

from ..config import Config
from ..driver import KernelDriver
from ..inventory import Inventory

DEFAULT_WAIT_TIMEOUT = 15

class Priority(object):
   DEFAULT = 0
   THERMAL = 0
   COOLING = 0
   BACKGROUND = 1
   POWER = 1
   LED = 1

   def priorityFilter(*priorities):
      return staticmethod(lambda component: component.priority in priorities)

   defaultFilter = priorityFilter(DEFAULT)
   backgroundFilter = priorityFilter(BACKGROUND)

class Component(object):
   def __init__(self, addr=None, priority=Priority.DEFAULT, drivers=None,
                inventoryCls=None, inventory=None, parent=None, **kwargs):
      super(Component, self).__init__()
      self.components = []
      self.addr = addr
      self.priority = priority
      self.drivers = OrderedDict()
      self.inventory = inventory
      self.parent = parent
      if not inventory and inventoryCls:
         self.inventory = inventoryCls()
      self.addDrivers(drivers)
      self.__dict__.update(kwargs)

   def __str__(self):
      kwargs = ['%s=%s' % (k, v) for k, v in self.__dict__.items()]
      return '%s(%s)' % (self.__class__.__name__, ', '.join(kwargs))

   def addComponents(self, components):
      assert all(isinstance(c, Component) for c in components)
      for component in components:
         component.priority = max(component.priority, self.priority)
         self.components.append(component)
      return self

   def addComponent(self, component):
      assert isinstance(component, Component)
      component.priority = max(component.priority, self.priority)
      self.components.append(component)
      return self

   def newComponent(self, cls, *args, **kwargs):
      inventory = Inventory() if Config().use_metainventory else self.inventory
      component = cls(inventory=inventory, *args, parent=self, **kwargs)
      self.addComponent(component)
      return component

   def iterComponents(self, filters=Priority.defaultFilter, recursive=True):
      if filters is None:
         filters = []
      if not hasattr(filters, '__iter__'):
         filters = [filters]
      allFilters = lambda x: all(f(x) for f in filters)

      for component in filter(allFilters, self.components):
         yield component
         if recursive:
            for sub in component.iterComponents(filters):
               yield sub

   def iterInventory(self, filters=None):
      for component in self.iterComponents(filters=filters):
         yield component.inventory

   def addDrivers(self, drivers):
      if drivers:
         for drv in drivers:
            key = getattr(drv, 'driverName', drv.__class__.__name__)
            if key not in self.drivers:
               self.drivers[key] = drv

   # Compatibility function for platform code
   def addDriver(self, driver, *args, **kwargs):
      if driver:
         if driver == KernelDriver:
            kwargs['module'] = args[0]
         drv = driver(**kwargs)
         self.drivers[getattr(drv, 'driverName', None) or
                      driver.__class__.__name__] = drv

   def getInventory(self):
      return self.inventory

   def setup(self):
      for driver in self.drivers.values():
         driver.setup()
      for driver in self.drivers.values():
         driver.finish()

   def finish(self, filters=Priority.defaultFilter):
      # underlying component are initialized recursively but require the parent to
      # be fully initialized
      for component in self.iterComponents(filters, recursive=False):
         component.setup()
      for component in self.iterComponents(recursive=False):
         component.finish(filters)

   def refresh(self):
      for component in self.components:
         component.refresh()
      for driver in self.drivers.values():
         driver.refresh()

   def clean(self):
      for component in self.components:
         component.clean()
      for driver in reversed(self.drivers.values()):
         driver.clean()

   def resetIn(self):
      for component in self.components:
         component.resetIn()
      for driver in reversed(self.drivers.values()):
         driver.resetIn()

   def resetOut(self):
      for driver in self.drivers.values():
         driver.resetOut()
      for component in self.components:
         component.resetOut()

   def getReloadCauses(self, clear=False):
      causes = []
      for driver in self.drivers.values():
         causes.extend(driver.getReloadCauses(clear=clear))
      for component in self.components:
         causes.extend(component.getReloadCauses(clear=clear))
      return causes

   def waitForIt(self, timeout=DEFAULT_WAIT_TIMEOUT):
      for component in self.components:
         component.waitForIt(timeout)

   def __diag__(self, ctx):
      return {}

   def genDiag(self, ctx):
      output = {
         "version": 1,
         "name": self.__class__.__name__,
         "data": self.__diag__(ctx),
         "drivers": [d.genDiag(ctx) for d in self.drivers.values()],
      }
      if self.inventory not in ctx.inventories:
         output["inventory"] = self.inventory.__diag__(ctx)
         ctx.inventories.add(self.inventory)
      else:
         output["inventory"] = None
      if ctx.recursive:
         output["components"] = [c.genDiag(ctx) for c in
                                 self.iterComponents(recursive=False)]
      else:
         output["components"] = []
      return output

class PciComponent(Component):
   # XXX: Legacy, use component.pci.PciComponent instead
   def __init__(self, **kwargs):
      super(PciComponent, self).__init__(**kwargs)

class I2cComponent(Component):
   # XXX: Legacy, use component.i2c.I2cComponent instead
   def __init__(self, **kwargs):
      super(I2cComponent, self).__init__(**kwargs)

   def __str__(self):
      return '%s(addr=%s)' % (self.__class__.__name__, self.addr)

class SlotComponent(Component):
   def getPresence(self):
      raise NotImplementedError
