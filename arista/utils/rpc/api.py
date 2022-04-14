"""Implements classes for defining the JSON-RPC API."""

try:
   import asyncio
except ImportError:
   print('This feature only works in python3')
   raise

from ...core.log import getLogger

logging = getLogger(__name__)

def registerMethod(method):
   method.isRpcMethod = True
   return method

class RpcApi():
   """An RpcApi object implements the functionality of the JSON-RPC API.

   The JSON-RPC server should call methods on this object to run the
   functionality associated with the method. A JSON-RPC client may use
   the `methods` class property to determine what JSON-RPC methods are
   supported."""

   _methods = []

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

   @classmethod
   def methods(cls):
      if not cls._methods:
         cls._methods = [n for n, m in cls.__dict__.items() if getattr(m, 'isRpcMethod', False)]
      return cls._methods
