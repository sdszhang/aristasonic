try:
   import asyncio
except ImportError:
   print('This feature only works in python3')
   raise

import json

from ...core.log import getLogger

from .api import RpcApi
from .constants import JsonRpcError, JSONRPC_VERSION

logging = getLogger(__name__)

class RpcServer():
   def __init__(self, host, port):
      self.api = RpcApi()
      self.host = host
      self.port = port

   async def start(self):
      await asyncio.start_server(self.handleConnection, self.host, self.port,
                                 reuse_port=True)

   def response(self, result, uid=None, id_present=True):
      return json.dumps({
         'jsonrpc': JSONRPC_VERSION,
         'result': result,
         'id': uid,
      }) if id_present else None

   def errorResponse(self, code, message, uid=None, id_present=True):
      return json.dumps({
         'jsonrpc': JSONRPC_VERSION,
         'error': {
            'code': code,
            'message': message,
         },
         'id': uid,
      }) if id_present else None

   async def handleRequest(self, request):
      uid = request.get('id', None)
      id_present = 'id' in request

      if request.get('jsonrpc') != JSONRPC_VERSION:
         return self.errorResponse(
            JsonRpcError.INTERNAL_ERROR,
            'This server only implements the JSON-RPC 2.0 protocol',
            uid=uid, id_present=id_present)

      if 'method' not in request:
         return self.errorResponse(JsonRpcError.INVALID_REQUEST,
                                   'Missing field "method"',
                                   uid=uid, id_present=id_present)

      methodName = request['method']
      if methodName not in list(self.api.methods()):
         return self.errorResponse(JsonRpcError.METHOD_NOT_FOUND,
                                   f'No such method "{methodName}"',
                                   uid=uid, id_present=id_present)
      method = getattr(self.api, methodName)

      params = request.get('params', None)
      try:
         result = None
         if params is None:
            result = await method()
         elif isinstance(params, list):
            result = await method(*params)
         elif isinstance(params, dict):
            result = await method(**params)
         else:
            return self.errorResponse(JsonRpcError.INVALID_PARAMS,
                                      'params is not array or object',
                                      uid=uid, id_present=id_present)
         return self.response(result, uid=uid, id_present=id_present)
      except TypeError as e:
         return self.errorResponse(JsonRpcError.INVALID_PARAMS,
                                   str(e),
                                   uid=uid, id_present=id_present)
      except Exception as e: #pylint: disable=broad-except
         return self.errorResponse(-1,
                                   str(e),
                                   uid=uid, id_present=id_present)

   async def handleConnection(self, reader, writer):
      addr = writer.get_extra_info('peername')
      try:
         data = b''
         while not reader.at_eof():
            data = await reader.read(4096)
            message = None
            try:
               message = json.loads(data)
            except ValueError:
               pass

            logging.info(f'Received {message!r} from {addr!r}')

            if message is None:
               response = self.errorResponse(JsonRpcError.PARSE_ERROR, 'Parse Error')
            elif isinstance(message, dict):
               response = await self.handleRequest(message)
            elif isinstance(message, list):
               response = await asyncio.gather(self.handleRequest(x) for x in message)
            else:
               response = json.dumps({
                  'jsonrpc': '2.0',
                  'error': {
                     'code': JsonRpcError.INVALID_REQUEST,
                     'message': 'JSON is not a valid JSON-RPC request',
                  },
                  'id': None
               })

            if response:
               response += '\n'
               writer.write(response.encode('utf-8'))
            else:
               logging.info('No response')
      except: # pylint: disable=bare-except
         logging.exception(f'Failed to handle request from {addr!r}')
         response = self.errorResponse(JsonRpcError.INTERNAL_ERROR,
                                       'Internal error',
                                       uid=None)
         if response:
            response += '\n'
            writer.write(response.encode('utf-8'))
      finally:
         writer.close()
