
import warnings

class InventoryInterface(object):
   def __diag__(self, ctx):
      warnings.warn('inventory objects should implement diag', DeprecationWarning)
      return {}

   def genDiag(self, ctx):
      desc = getattr(self, 'desc', None)
      return {
         "version": 1,
         "name": self.__class__.__name__,
         "desc": desc.__diag__(ctx) if desc else {},
         "data": self.__diag__(ctx),
      }
