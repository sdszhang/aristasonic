
from ...core.cpu import Cpu
from ...core.pci import PciRoot
from ...core.supervisor import Supervisor

class MockCpu(Cpu):
   def __init__(self):
      super(Cpu, self).__init__()
      self.pciRoot = PciRoot()

class MockSupervisor(Supervisor):
   def addCpuComplex(self):
      self.cpu = MockCpu()
