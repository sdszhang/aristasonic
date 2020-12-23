
from ...core.supervisor import Supervisor

from ..args.dump import dumpParser
from .diag import doCommonDiagCli

from . import registerAction

class DiagArgs(object):
   def __init__(self, noIo=False, recursive=True, pyshell=False, pretty=True):
      self.noIo = noIo
      self.recursive = recursive
      self.pyshell = pyshell
      self.pretty = pretty

@registerAction(dumpParser)
def doDump(ctx, args):
   args = DiagArgs()
   skus = []
   if isinstance(ctx.platform, Supervisor):
      chassis = ctx.platform.getChassis()
      chassis.loadAll()
      skus.append(chassis)
   else:
      skus.append(ctx.platform)
   doCommonDiagCli(skus, args)
