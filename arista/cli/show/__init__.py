
from __future__ import print_function

class Renderer():

   NAME = None

   def __init__(self, name=None):
      self.name = name or self.NAME

   def renderText(self, show):
      raise NotImplementedError

   def data(self, show):
      '''Output for JSON, recommended to use for text as well'''
      raise NotImplementedError

class Show():

   TXT = 'text'
   JSON = 'json'

   def __init__(self, outputFormat=None, args=None):
      self.outputFormat = outputFormat
      self.inventories = []
      self.args = args
      self.platform = None

   def addInventory(self, inventory, **metadata):
      self.inventories.append((inventory, metadata))

   def addPlatform(self, platform):
      self.platform = platform

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
