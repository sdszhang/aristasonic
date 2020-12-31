
from ..core.component import Priority
from ..core.component.pci import PciComponent

from ..drivers.microsemi import MicrosemiDriver
from ..drivers.pci import PciSwitchPortDriver

class MicrosemiPortDesc(object):
   def __init__(self, port, dsp, partition):
      self.port = port
      self.dsp = dsp
      self.partition = partition

class MicrosemiPort(PciComponent):

   DRIVER = PciSwitchPortDriver
   PRIORITY = Priority.DEFAULT

   def __init__(self, desc=None, addr=None, **kwargs):
      super(MicrosemiPort, self).__init__(addr=addr, **kwargs)
      self.desc = desc

   def enable(self):
      self.driver.enable()

   def disable(self):
      self.driver.disable()

class Microsemi(PciComponent):

   DRIVER = MicrosemiDriver
   PRIORITY = Priority.DEFAULT

   def __init__(self, ports=None, **kwargs):
      super(Microsemi, self).__init__(**kwargs)
      self.ports = ports or {}

   def addPciPort(self, portId=None, desc=None, addr=None, upstreamAddr=None):
      port = self.newComponent(
         MicrosemiPort,
         desc=desc,
         addr=addr,
         upstreamAddr=upstreamAddr,
      )
      self.ports[portId] = port
      return port

   def bind(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      portDesc = self.ports[slotId].desc
      return self.driver.bind(portDesc.port, portDesc.dsp, portDesc.partition)

   def unbind(self, slotId, flags=0x2):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      portDesc = self.ports[slotId].desc
      return self.driver.unbind(portDesc.dsp, portDesc.partition, flags=flags)

   def enable(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      self.ports[slotId].enable()

   def disable(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      self.ports[slotId].disable()
