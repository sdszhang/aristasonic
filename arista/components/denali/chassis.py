
from ...core.modular import Modular

from .card import DenaliCard, DenaliCardSlot

class DenaliChassis(Modular):
   CARD_SLOT_CLS = DenaliCardSlot
   CARD_CLS = DenaliCard

   NUM_SUPERVISORS = 2
