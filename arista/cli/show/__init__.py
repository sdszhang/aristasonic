
from __future__ import print_function

def getKey(data, key, default="N/A"):
   try:
      for member in key.split('.'):
         member = int(member) if member.isdigit() else member
         data = data[member]
   except Exception: # pylint: disable=broad-except
      data = default
   return data

def tupleFmt(data, fmt, *args):
   return fmt % tuple(getKey(data, k) for k in args)


class Col():
   def __init__(self, name, attr, size):
      self.name = name
      self.attr = attr
      self.size = size

class Table():
   def __init__(self, columns):
      self.columns = columns

   def render(self, data, newline=False):
      if not data:
         return

      fmt = ' '.join('%%-%ds' % c.size for c in self.columns)
      print(fmt % tuple(c.name for c in self.columns))
      print(fmt % tuple('-' * c.size for c in self.columns))
      for item in data:
         print(fmt % tuple(getKey(item, c.attr) for c in self.columns))

      if newline:
         print()

class Renderer():

   NAME = None

   def __init__(self, name=None):
      self.name = name or self.NAME
      self.data_ = {}

   def data(self, show):
      data = self.data_.get(show)
      if data is None:
         data = self.getData(show)
         self.data_[show] = data
      return data

   def getData(self, show):
      '''Output for JSON, recommended to use as source for renderText'''
      raise NotImplementedError

   def renderText(self, show):
      '''Textual output for CLI'''
      raise NotImplementedError

class Show():

   TXT = 'text'
   JSON = 'json'

   def __init__(self, outputFormat=None, args=None):
      self.outputFormat = outputFormat
      self.inventories = []
      self.platforms = []
      self.args = args

   def addInventory(self, inventory, **metadata):
      self.inventories.append((inventory, metadata))

   def addPlatform(self, platform):
      self.platforms.append(platform)

   def renderText(self, *renderers):
      for r in renderers:
         r.renderText(self)

   def renderJson(self, *renderers):
      data = {
         "version": 1,
         "renderers": {
            r.name : r.data(self) for r in renderers
         },
      }

      import json
      if self.args.pretty:
         print(json.dumps(data, indent=3, separators=(',', ': ')))
      else:
         print(json.dumps(data))

   def render(self, *renderers):
      if self.outputFormat == self.TXT:
         self.renderText(*renderers)
      elif self.outputFormat == self.JSON:
         self.renderJson(*renderers)
