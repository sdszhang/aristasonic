
from __future__ import print_function

from ...core.diag import DiagContext

from . import Renderer

class ShowEnvironment(Renderer):
   def __init__(self):
      super(ShowEnvironment, self).__init__('environment')

   def data(self, show):
      ctx = DiagContext()
      data = {
         'fans': [],
         'temps': [],
         'psuSlots': [],
      }
      for inventory, _ in show.inventories:
         for temp in inventory.getTemps():
            data['temps'].append(temp.__diag__(ctx))
         for fan in inventory.getFans():
            data['fans'].append(fan.__diag__(ctx))
         for slot in inventory.getPsuSlots():
            data['psuSlots'].append(slot.__diag__(ctx))
      return data

   def _getKey(self, data, key, default="N/A"):
      try:
         for member in key.split('.'):
            data = data[member]
      except Exception: # pylint: disable=broad-except
         data = default
      return data

   def _renderCollection(self, hdr, collection):
      if not collection:
         return

      fmt = ' '.join('%%-%ds' % sz for _, _, sz in hdr)
      print(fmt % tuple(n for n, _, _ in hdr))
      print(fmt % tuple('-' * sz for _, _, sz in hdr))
      for item in collection:
         print(fmt % tuple(self._getKey(item, k) for _, k, _ in hdr))

   def renderText(self, show):
      data = self.data(show)

      tempHdr = [
         ('Name', 'name', 40),
         ('Temp', 'value', 8),
         ('Alert', 'highThresh', 8),
         ('Critical', 'highCritThresh', 8),
      ]
      fanHdr = [
         ('Name', 'name', 10),
         ('Model', 'model', 15),
         ('Status', 'status', 6),
         ('Speed', 'speed', 4),
      ]
      psuHdr = [
         ('Name', 'name', 10),
         ('Model', 'psu.model', 15),
         ('Serial', 'psu.serial', 15),
         ('Status', 'status', 6),
      ]

      self._renderCollection(tempHdr, data['temps'])
      print()
      self._renderCollection(fanHdr, data['fans'])
      print()
      self._renderCollection(psuHdr, data['psuSlots'])
