
from ..components.xcvr import Osfp, Qsfp, Sfp
from ..inventory.xcvr import (
   Osfp as OsfpInv,
   OsfpSlot as OsfpSlotInv,
   Qsfp as QsfpInv,
   QsfpSlot as QsfpSlotInv,
   Sfp as SfpInv,
   SfpSlot as SfpSlotInv,
)
from .component import SlotComponent

class SfpImpl(SfpInv):
   def __init__(self, addrFunc, slot):
      self.addr = addrFunc(self.ADDR)
      self.slot = slot

   def getType(self):
      return "sfp"

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getI2cAddr(self):
      return self.addr

class QsfpImpl(QsfpInv):
   def __init__(self, addrFunc, slot):
      self.addr = addrFunc(self.ADDR)
      self.slot = slot

   def getType(self):
      return "qsfp"

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getI2cAddr(self):
      return self.addr

class OsfpImpl(OsfpInv):
   def __init__(self, addrFunc, slot):
      self.addr = addrFunc(self.ADDR)
      self.slot = slot

   def getType(self):
      return "osfp"

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getI2cAddr(self):
      return self.addr

class SfpSlotImpl(SfpSlotInv):
   def __init__(self, slot):
      self.slot = slot

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getPresence(self):
      return self.slot.getPresence()

   def getLeds(self):
      return self.slot.leds

   def getInterruptLine(self):
      return self.slot.getInterruptLine()

   def getReset(self):
      # Not supported for SFP
      return None

   def getLowPowerMode(self):
      # Not supported for SFP
      return False

   def setLowPowerMode(self, value):
      # Not supported for SFP
      return False

   def getModuleSelect(self):
      # Not supported for SFP
      return True

   def setModuleSelect(self, value):
      # Not supported for SFP
      return True

   def getRxLos(self):
      return self.slot.getRxLos()

   def getTxDisable(self):
      return self.slot.getTxDisable()

   def setTxDisable(self, value):
      return self.slot.setTxDisable(value)

   def getTxFault(self):
      return self.slot.getTxFault()

   def getXcvr(self):
      return self.slot.getXcvr()

class QsfpSlotImpl(QsfpSlotInv):
   def __init__(self, slot):
      self.slot = slot

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getPresence(self):
      return self.slot.getPresence()

   def getLeds(self):
      return self.slot.leds

   def getInterruptLine(self):
      return self.slot.getInterruptLine()

   def getReset(self):
      return self.slot.getReset()

   def getLowPowerMode(self):
      return self.slot.getLowPowerMode()

   def setLowPowerMode(self, value):
      return self.slot.setLowPowerMode(value)

   def getModuleSelect(self):
      return self.slot.getModuleSelect()

   def setModuleSelect(self, value):
      return self.slot.setModuleSelect(value)

   def getRxLos(self):
      # Not supported for QSFP
      return False

   def getTxDisable(self):
      # Not supported for QSFP
      return False

   def setTxDisable(self, value):
      # Not supported for QSFP
      return False

   def getTxFault(self):
      # Not supported for QSFP
      return False

   def getXcvr(self):
      return self.slot.getXcvr()

class OsfpSlotImpl(OsfpSlotInv):
   def __init__(self, slot):
      self.slot = slot

   def getId(self):
      return self.slot.getId()

   def getName(self):
      return self.slot.getName()

   def getPresence(self):
      return self.slot.getPresence()

   def getLeds(self):
      return self.slot.leds

   def getInterruptLine(self):
      return self.slot.getInterruptLine()

   def getReset(self):
      return self.slot.getReset()

   def getLowPowerMode(self):
      return self.slot.getLowPowerMode()

   def setLowPowerMode(self, value):
      return self.slot.setLowPowerMode(value)

   def getModuleSelect(self):
      return self.slot.getModuleSelect()

   def setModuleSelect(self, value):
      return self.slot.setModuleSelect(value)

   def getRxLos(self):
      # Not supported for OSFP
      return False

   def getTxDisable(self):
      # Not supported for OSFP
      return False

   def setTxDisable(self, value):
      # Not supported for OSFP
      return False

   def getTxFault(self):
      # Not supported for OSFP
      return False

   def getXcvr(self):
      return self.slot.getXcvr()

class XcvrSlot(SlotComponent):
   def __init__(self, slotId=None, name=None, addrFunc=None, interrupt=None,
                presentGpio=None, leds=None, **kwargs):
      super(XcvrSlot, self).__init__(**kwargs)
      self.addrFunc = addrFunc
      self.slotId = slotId
      self.name = name
      self.interrupt = interrupt
      self.presentGpio = presentGpio
      self.leds = leds
      self.xcvr = None

   def getId(self):
      return self.slotId

   def getName(self):
      return self.name

   def getPresence(self):
      return self.presentGpio.isActive()

   def getInterruptLine(self):
      return self.interrupt

   def getXcvr(self):
      return self.xcvr

   def getLeds(self):
      return self.leds

class SfpSlot(XcvrSlot):
   def __init__(self, rxLosGpio=None, txDisableGpio=None, txFaultGpio=None,
                **kwargs):
      super(SfpSlot, self).__init__(**kwargs)
      self.rxLosGpio = rxLosGpio
      self.txDisableGpio = txDisableGpio
      self.txFaultGpio = txFaultGpio
      self.sfpSlotInv = self.inventory.addSfpSlot(SfpSlotImpl(self))
      self.addSfp()

   def addSfp(self):
      self.xcvr = self.inventory.addSfp(SfpImpl(self.addrFunc, self.sfpSlotInv))
      self.newComponent(
         cls=Sfp,
         addr=self.xcvr.getI2cAddr(),
         portName=self.name
      )

   def getTxDisable(self):
      return self.txDisableGpio.isActive()

   def setTxDisable(self, value):
      return self.txDisableGpio.setActive(value)

   def getTxFault(self):
      return self.txFaultGpio.isActive()

   def getRxLos(self):
      return self.rxLosGpio.isActive()

class QsfpSlot(XcvrSlot):
   def __init__(self, lpMode=None, modSel=None, reset=None, **kwargs):
      super(QsfpSlot, self).__init__(**kwargs)
      self.lpMode = lpMode
      self.modSel = modSel
      self.reset = reset

      self.qsfpSlotInv = self.inventory.addQsfpSlot(QsfpSlotImpl(self))
      self.addQsfp()

   def addQsfp(self):
      self.xcvr = self.inventory.addQsfp(QsfpImpl(self.addrFunc, self.qsfpSlotInv))
      self.newComponent(
         cls=Qsfp,
         addr=self.xcvr.getI2cAddr(),
         portName=self.name
      )

   def getReset(self):
      return self.reset

   def getLowPowerMode(self):
      if not self.lpMode:
         # Indicates that a platform does not have HW support for lp mode
         raise NotImplementedError
      return self.lpMode.isActive()

   def setLowPowerMode(self, value):
      if not self.lpMode:
         raise NotImplementedError
      return self.lpMode.setActive(value)

   def getModuleSelect(self):
      if not self.modSel:
         raise NotImplementedError
      return self.modSel.isActive()

   def setModuleSelect(self, value):
      if not self.modSel:
         raise NotImplementedError
      return self.modSel.setActive(value)

class OsfpSlot(XcvrSlot):
   def __init__(self, lpMode=None, modSel=None, reset=None, **kwargs):
      super(OsfpSlot, self).__init__(**kwargs)
      self.lpMode = lpMode
      self.modSel = modSel
      self.reset = reset
      self.osfpSlotInv = self.inventory.addOsfpSlot(OsfpSlotImpl(self))
      self.addOsfp()

   def addOsfp(self):
      self.xcvr = self.inventory.addOsfp(OsfpImpl(self.addrFunc, self.osfpSlotInv))
      self.newComponent(
         cls=Osfp,
         addr=self.xcvr.getI2cAddr(),
         portName=self.name
      )

   def getReset(self):
      return self.reset

   def getLowPowerMode(self):
      if not self.lpMode:
         raise NotImplementedError
      return self.lpMode.isActive()

   def setLowPowerMode(self, value):
      if not self.lpMode:
         raise NotImplementedError
      return self.lpMode.setActive(value)

   def getModuleSelect(self):
      if not self.modSel:
         raise NotImplementedError
      return self.modSel.isActive()

   def setModuleSelect(self, value):
      if not self.modSel:
         raise NotImplementedError
      return self.modSel.setActive(value)
