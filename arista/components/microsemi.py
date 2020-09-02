
from .common import PciComponent
from ..drivers.microsemi import MicrosemiDriver
from ..drivers.pci import PciSwitchPortDriver

class MicrosemiPortDesc(object):
   def __init__(self, port, dsp, partition):
      self.port = port
      self.dsp = dsp
      self.partition = partition

class MicrosemiPort(PciComponent):
   def __init__(self, desc, addr=None, upstreamAddr=None, drivers=None, **kwargs):
      drivers = drivers or [
         PciSwitchPortDriver(addr=addr, upstreamAddr=upstreamAddr)
      ]
      super(MicrosemiPort, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.desc = desc
      self.upstreamAddr = upstreamAddr

   def enable(self):
      self.drivers['PciSwitchPortDriver'].enable()

   def disable(self):
      self.drivers['PciSwitchPortDriver'].disable()

class Microsemi(PciComponent):
   def __init__(self, addr=None, drivers=None, ports=None, **kwargs):
      drivers = drivers or [MicrosemiDriver(addr=addr)]
      super(Microsemi, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.ports = ports

   def bind(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      portDesc = self.ports[slotId].desc
      return self.drivers['MicrosemiDriver'].bind(portDesc.port, portDesc.dsp,
                                                  portDesc.partition)

   def unbind(self, slotId, flags=0x2):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      portDesc = self.ports[slotId].desc
      return self.drivers['MicrosemiDriver'].unbind(portDesc.dsp, portDesc.partition,
                                                    flags=flags)

   def enable(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      self.ports[slotId].enable()

   def disable(self, slotId):
      assert slotId in self.ports, \
             "SlotId %d is not defined in downstream ports" % slotId
      self.ports[slotId].disable()
