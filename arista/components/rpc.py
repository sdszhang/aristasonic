
from ..core.component.component import Component
from ..drivers.rpc import LinecardRpcClientDriver

class LinecardRpcClient(Component):
   DRIVER = LinecardRpcClientDriver
