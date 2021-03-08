
from collections import namedtuple

from .common import I2cComponent
from ..core.register import RegisterMap, Register, RegBitField, RegBitRange
from ..drivers.plx import PlxPex8700I2cDevDriver

PlxPortDesc = namedtuple('PlxPortDesc', [
   'port',
   'lane',
   'name',
])

class PlxPort(object):
   def __init__(self, plx, pciePort, pcieLane, name):
      self.plx = plx
      self.pciePort = pciePort
      self.pcieLane = pcieLane
      self.name = name

   def enable(self):
      return self.plx.enablePort(self)

   def disable(self):
      return self.plx.disablePort(self)

class Plx(I2cComponent):
   def __init__(self, addr, reverse=False, drivers=None, **kwargs):
      super(Plx, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.ports = []
      self.reverse = reverse

   def addPorts(self, ports):
      for port in ports:
         self.ports.append(PlxPort(self, port.port, port.lane, port.name))

   def get(self, name):
      port = [p for p in self.ports if p.name == name]
      if len(port) != 1:
         return None
      return port[0]

   def enablePort(self, port):
      raise NotImplementedError

   def disablePort(self, port):
      raise NotImplementedError

class Plx8700RegisterMap(RegisterMap):
   SltCap = Register(0x7c,
      RegBitField(5, 'hotPlugSurprise', ro=False),
      RegBitField(6, 'hotPlugCapable', ro=False),
   )

   PortDisable = Register(0x208, name="portDisable")

   Vs0Upstream = Register(0x360,
      RegBitRange(0, 4, 'upstreamPort', ro=False),
      RegBitRange(8, 12, 'ntPort', ro=False),
      RegBitField(13, 'ntEnable', ro=False),
   )

   Vs0PortVec = Register(0x380, name="vs0PortVec")
   Vs1PortVec = Register(0x384, name="vs1PortVec")

class PlxPex8700(Plx):
   def __init__(self, addr, reverse=False, drivers=None,
                registerCls=None, **kwargs):
      if not drivers:
         drivers = [PlxPex8700I2cDevDriver(addr=addr,
                                           registerCls=Plx8700RegisterMap)]
      super(PlxPex8700, self).__init__(addr=addr, reverse=reverse,
                                       drivers=drivers, **kwargs)

   def enableHotPlug(self):
      self.drivers['PlxPex8700I2cDevDriver'].enableHotPlug()

   def disableUpstreamPort(self, port, off=True):
      self.drivers['PlxPex8700I2cDevDriver'].disableUpstreamPort(port, off)

   def setUpstreamPort(self, port=0):
      self.drivers['PlxPex8700I2cDevDriver'].setUpstreamPort(port)

   def setNtPort(self, port=2):
      self.drivers['PlxPex8700I2cDevDriver'].setNtPort(port)

   def enableNt(self, on=False):
      self.drivers['PlxPex8700I2cDevDriver'].enableNt(on)

   def smbusPing(self):
      return self.drivers['PlxPex8700I2cDevDriver'].smbusPing()

   def vsPortVec(self, vsId, value=None):
      return self.drivers['PlxPex8700I2cDevDriver'].vsPortVec(vsId, value)
