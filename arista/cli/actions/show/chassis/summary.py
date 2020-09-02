
from __future__ import absolute_import, division, print_function

from . import registerAction
from ....args.show.chassis.summary import chassisSummaryParser
from .....core.prefdl import InvalidPrefdlData

def doShowCard(ctx, args, card):
   try:
      if card and card.slot.getPresence():
         eeprom = card.slot.getEeprom()
         sku = eeprom.get('SKU')
         serial = eeprom.get('SerialNumber')
         print("  %d: %s (%s)" % (card.slot.slotId, sku, serial))
      else:
         print("  %d: not present" % card.slot.slotId)
   except InvalidPrefdlData:
      print("  %d: invalid prefdl" % card.slot.slotId)
   except IOError:
      print("  %d: IO Error" % card.slot.slotId)

@registerAction(chassisSummaryParser)
def doChassisSummary(ctx, args):
   eeprom = ctx.chassis.getEeprom()
   print("Sku: %s" % eeprom.get('SKU'))
   print("Serial: %s" % eeprom.get('SerialNumber'))
   print("Linecards:")
   for linecard in ctx.chassis.iterLinecards():
      doShowCard(ctx, args, linecard)
   print("Fabrics:")
   for fabric in ctx.chassis.iterFabrics():
      doShowCard(ctx, args, fabric)

