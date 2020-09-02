
from __future__ import absolute_import, division, print_function

from .. import registerAction
from ...args.fabric.setup import setupParser
from ....core.component import Priority
from ....core.log import getLogger

logging = getLogger(__name__)

@registerAction(setupParser)
def doSetup(ctx, args):
   for fabric in ctx.fabrics:
      logging.debug('Setting up %s', fabric)
      try:
         if args.early or not args.late:
            fabric.setup(Priority.defaultFilter)
         if args.late or not args.early:
            fabric.setup(Priority.backgroundFilter)
         if args.on:
            fabric.powerOnIs(True)
            if args.early or not args.late:
               fabric.setupMain(Priority.defaultFilter)
            if args.late or not args.early:
               fabric.setupMain(Priority.backgroundFilter)
      except Exception as e:
         logging.warning('Failed to setup %s: %s', fabric, str(e))

