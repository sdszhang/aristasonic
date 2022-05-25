from ..core.daemon import registerDaemonFeature, OneShotFeature
from ..core.config import Config
from ..core.log import getLogger
from ..core.supervisor import Supervisor
from ..utils.rpc.server import RpcServer

logging = getLogger(__name__)

@registerDaemonFeature()
class JsonRpcDaemonFeature(OneShotFeature):
   NAME = 'jsonrpc'

   def __init__(self):
      OneShotFeature.__init__(self)
      self.server = None

   def run(self):
      if isinstance(self.daemon.platform, Supervisor):
         logging.info('%s: setting up server on supervisor', self)
         hosts = [Config().api_rpc_host, Config().api_rpc_sup]
         port = Config().api_rpc_port
         self.server = RpcServer(hosts, port, self.daemon.platform)
         self.daemon.loop.create_task(self.server.start())
      else:
         logging.info('%s: not supervisor, nothing to do')
