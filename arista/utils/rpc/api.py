"""Implements classes for defining the JSON-RPC API."""

try:
   import asyncio
except ImportError:
   print('This feature only works in python3')
   raise

from ...core.cause import getLinecardReloadCauseManager
from ...core.log import getLogger
from ...core.supervisor import Supervisor

logging = getLogger(__name__)

class RpcPermissionError(Exception):
   pass

def registerMethod(method):
   def wrapper(self, ctx, *args, **kwargs):
      if not ctx.localhost():
         raise RpcPermissionError('method only available from localhost')
      return method(self, *args, *kwargs)
   wrapper.isRpcMethod = True
   return wrapper

def registerLinecardMethod(method):
   def wrapper(self, ctx, *args, **kwargs):
      if not isinstance(self.platform, Supervisor):
         raise RpcPermissionError('method only available on chassis systems')

      slotId = ctx.slotId()
      if slotId is None:
         raise RpcPermissionError('method only available for linecards')

      try:
         offset = self.platform.linecardSlots[0].card.ABSOLUTE_CARD_OFFSET
         slot = self.platform.linecardSlots[slotId - offset]
      except IndexError:
         raise RpcPermissionError(f'linecard {slotId} is not available')

      # NOTE: Making sure we have the latest platform definition loaded would
      #       be the best, however we need need to check for leaks before doing
      #       so. We should not allow the daemon to grow in size over time.
      # slot.loadCard(standbyOnly=True)
      lc = slot.card
      return method(self, lc, *args, **kwargs)
   wrapper.isRpcMethod = True
   return wrapper

class RpcApi():
   """An RpcApi object implements the functionality of the JSON-RPC API.

   The JSON-RPC server should call methods on this object to run the
   functionality associated with the method. A JSON-RPC client may use
   the `methods` class property to determine what JSON-RPC methods are
   supported."""

   _methods = []

   def __init__(self, platform=None):
      self.platform = platform

   async def _runCommand(self, cmd, *args):
      proc = await asyncio.create_subprocess_exec(
         cmd, *args,
         stdout=asyncio.subprocess.PIPE,
         stderr=asyncio.subprocess.PIPE)

      stdout, stderr = await proc.communicate()

      logging.info(f'Command [{cmd} {" ".join(args)}] exited with {proc.returncode}')

      return {'status': proc.returncode == 0,
              'detail': '\n'.join([stdout.decode('utf-8'),
                                   stderr.decode('utf-8')])}

   async def _runAristaFabric(self, slot, *args):
      allArgs = ['-l', '/var/log/arista-fabric.log',
                 'fabric', '-i', str(slot)]
      allArgs.extend(args)
      return await self._runCommand('arista', *allArgs)

   async def _runAristaLinecard(self, slot, *args):
      allArgs = ['-l', '/var/log/arista-linecard.log',
                 'linecard', '-i', str(slot)]
      allArgs.extend(args)
      return await self._runCommand('arista', *allArgs)

   @registerMethod
   async def linecardSetup(self, slot):
      """Power on the linecard identified by slot.

      This method returns a dictionary with two elements:
        - status: True if the command succeeded, false otherwise.
        - detail: Any output produced by the power on command."""
      return await self._runAristaLinecard(slot, 'setup', '--lcpu', '--on')

   @registerMethod
   async def linecardClean(self, slot):
      """Power off the linecard identified by slot.

      This method returns a dictionary with two elements:
        - status: True if the command succeeded, false otherwise.
        - detail: Any output produced by the power off command."""
      return await self._runAristaLinecard(slot, 'clean', '--lcpu', '--off')

   @registerMethod
   async def fabricSetup(self, slot):
      """Power on the fabric card identified by slot.

      This method returns a dictionary with two elements:
        - status: True if the command succeeded, false otherwise.
        - detail: Any output produced by the power on command."""
      return await self._runAristaFabric(slot, 'setup', '--on')

   @registerMethod
   async def fabricClean(self, slot):
      """Power off the fabric card identified by slot.

      This method returns a dictionary with two elements:
        - status: True if the command succeeded, false otherwise.
        - detail: Any output produced by the power off command."""
      return await self._runAristaFabric(slot, 'clean')

   @registerLinecardMethod
   async def linecardStatusLedColorGet(self, lc):
      return lc.getInventory().getLed('status').getColor()

   @registerLinecardMethod
   async def linecardStatusLedColorSet(self, lc, color):
      return lc.getInventory().getLed('status').setColor(color)

   @registerLinecardMethod
   async def linecardPowerCycle(self, lc):
      cmd = ('setup', '--on', '--lcpu', '--powerCycleIfOn')
      return await self._runAristaLinecard(lc.getSlotId(), *cmd)

   @registerLinecardMethod
   async def getLinecardRebootCause(self, lc):
      return getLinecardReloadCauseManager(lc).toDict()

   @classmethod
   def methods(cls):
      if not cls._methods:
         cls._methods = [n for n, m in cls.__dict__.items() if getattr(m, 'isRpcMethod', False)]
      return cls._methods
