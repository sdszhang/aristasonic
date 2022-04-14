import json

from ....tests.testing import mock, unittest

from ..constants import JsonRpcError, JSONRPC_VERSION
from ..server import RpcServer

class RpcServerTest(unittest.IsolatedAsyncioTestCase):
   HOST = 'localhost'
   PORT = 42000

   def _testErrorResult(self, result_dict, expected_id, expected_code):
      self.assertEqual(set(result_dict.keys()),
                       set(['jsonrpc', 'id', 'error']))
      self.assertEqual(result_dict['jsonrpc'], JSONRPC_VERSION)
      if expected_id is not None:
         self.assertEqual(result_dict['id'], expected_id)
      self.assertEqual(result_dict['error']['code'], expected_code)
      self.assertEqual(set(result_dict['error'].keys()),
                       set(['code', 'message']))

   async def testHandleRequest(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      with mock.patch.object(server.api, 'linecardSetup') as mockObj:
         method_result = {
            'status': True,
            'detail': None
         }
         mockObj.return_value = method_result
         result = await server.handleRequest({
            'jsonrpc': JSONRPC_VERSION,
            'id': 5,
            'method': 'linecardSetup',
            'params': [7],
         })
         mockObj.assert_called_once_with(7)
         self.assertEqual(json.loads(result), {
            'jsonrpc': JSONRPC_VERSION,
            'id': 5,
            'result': method_result
         })

   async def testHandleRequestNoSuchMethod(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      result = await server.handleRequest({
         'jsonrpc': JSONRPC_VERSION,
         'id': 5,
         'method': 'methodThatDoesNotExist',
         'params': [7],
      })
      self._testErrorResult(json.loads(result), 5, JsonRpcError.METHOD_NOT_FOUND)

   async def testHandleRequestMethodFieldMissing(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      result = await server.handleRequest({
         'jsonrpc': JSONRPC_VERSION,
         'id': 5,
         'params': [7],
      })
      self._testErrorResult(json.loads(result), 5, JsonRpcError.INVALID_REQUEST)

   async def testHandleRequestVersionFieldMissing(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      result = await server.handleRequest({
         'id': 5,
         'method': 'linecardSetup',
         'params': [7],
      })
      self._testErrorResult(json.loads(result), 5, JsonRpcError.INTERNAL_ERROR)

   async def testHandleRequestParamsMissing(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      with mock.patch.object(server.api, 'linecardSetup'):
         result = await server.handleRequest({
            'jsonrpc': JSONRPC_VERSION,
            'id': 5,
            'method': 'linecardSetup',
            'params': None,
         })
      self._testErrorResult(json.loads(result), 5, JsonRpcError.INVALID_PARAMS)

   async def testHandleRequestRaise(self):
      server = RpcServer(RpcServerTest.HOST, RpcServerTest.PORT)
      with mock.patch.object(server.api, 'linecardSetup') as mockObj:
         mockObj.side_effect = Exception('fake test exception')
         result = await server.handleRequest({
            'jsonrpc': JSONRPC_VERSION,
            'id': 5,
            'method': 'linecardSetup',
            'params': None,
         })
      self._testErrorResult(json.loads(result), 5, -1)


if __name__ == '__main__':
   unittest.main()
