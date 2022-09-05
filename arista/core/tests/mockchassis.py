
from ...core.cpu import Cpu
from ...core.pci import PciRoot
from ...core.supervisor import Supervisor

from ...components.scd import Scd

class MockCpu(Cpu):
   def __init__(self):
      super(Cpu, self).__init__()
      self.pciRoot = PciRoot()
      scdPort = self.pciRoot.rootPort(bus=0x0f)
      self.scd = self.pciRoot.newComponent(Scd, addr=scdPort.addr)

class MockSupervisor(Supervisor):
   def addCpuComplex(self):
      self.cpu = MockCpu()

   def getPciPort(self, bus):
      return self.cpu.pciRoot.rootPort(bus=bus)

   def getSmbus(self, bus):
      return self.cpu.scd.getSmbus(bus)
