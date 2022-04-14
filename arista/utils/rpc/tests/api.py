try:
   import asyncio
except ImportError:
   print('This feature only works in python3')
   raise

from ....tests.testing import mock, unittest

from ..api import RpcApi

class FakeProcess():
   async def communicate(self):
      self.returncode = 0
      return b'This is stdout', b'This is stderr'

class ClientTest(unittest.IsolatedAsyncioTestCase):
   async def testLinecardSetup(self):
      api = RpcApi()
      with mock.patch('asyncio.create_subprocess_exec') as mockObj:
         mockObj.side_effect = lambda *args, **kwargs: FakeProcess()
         result = await api.linecardSetup(7)
         mockObj.assert_called_once_with('arista', '-l', '/var/log/arista-linecard.log',
                                         'linecard', '-i', '7', 'setup', '--lcpu', '--on',
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
         self.assertEqual(result, {
            'status': True,
            'detail': 'This is stdout\nThis is stderr'
         })

   async def testLinecardClean(self):
      api = RpcApi()
      with mock.patch('asyncio.create_subprocess_exec') as mockObj:
         mockObj.side_effect = lambda *args, **kwargs: FakeProcess()
         result = await api.linecardClean(7)
         mockObj.assert_called_once_with('arista', '-l', '/var/log/arista-linecard.log',
                                         'linecard', '-i', '7', 'clean', '--lcpu', '--off',
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
         self.assertEqual(result, {
            'status': True,
            'detail': 'This is stdout\nThis is stderr'
         })

   async def testFabricSetup(self):
      api = RpcApi()
      with mock.patch('asyncio.create_subprocess_exec') as mockObj:
         mockObj.side_effect = lambda *args, **kwargs: FakeProcess()
         result = await api.fabricSetup(54)
         mockObj.assert_called_once_with('arista', '-l', '/var/log/arista-fabric.log',
                                         'fabric', '-i', '54', 'setup', '--on',
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
         self.assertEqual(result, {
            'status': True,
            'detail': 'This is stdout\nThis is stderr'
         })

   async def testFabricClean(self):
      api = RpcApi()
      with mock.patch('asyncio.create_subprocess_exec') as mockObj:
         mockObj.side_effect = lambda *args, **kwargs: FakeProcess()
         result = await api.fabricClean(54)
         mockObj.assert_called_once_with('arista', '-l', '/var/log/arista-fabric.log',
                                         'fabric', '-i', '54', 'clean',
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
         self.assertEqual(result, {
            'status': True,
            'detail': 'This is stdout\nThis is stderr'
         })

if __name__ == '__main__':
   unittest.main()
