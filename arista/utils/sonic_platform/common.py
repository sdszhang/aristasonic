try:
   from arista.core.config import Config
   from arista.utils.rpc.client import RpcClient
except ImportError as e:
   raise ImportError("%s - Required module not found" % e)

_globalRpcClient = None

def getGlobalRpcClient():
   global _globalRpcClient
   if _globalRpcClient is None:
      _globalRpcClient = RpcClient(Config().api_rpc_host, Config().api_rpc_port)
   return _globalRpcClient
