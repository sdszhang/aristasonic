from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.psu import PsuSlot
from ..core.types import PciAddr
from ..core.utils import incrange

from ..components.asic.xgs.trident3 import Trident3
from ..components.scd import Scd

@registerPlatform()
class PikeZ(FixedSystem):
    # TODO: Cpu
    # TODO: Fans
    # TODO: PSUs
    # TODO: resets

    SID = ['PikeIslandZ']
    SKU = ['CCS-720DT-48S']

    PORTS = PortLayout(
        ethernets=incrange(1, 48),
        sfps=incrange(49, 52),
    )

    def __init__(self):
        super().__init__()

        # self.cpu = self.newComponent(PrairieCpu)
        scd = self.newComponent(Scd, PciAddr(device=0x18, func=7))
        self.scd = scd
        scd.createWatchdog()
        scd.createPowerCycle()
        scd.addSmbusMasterRange(0x8000, 0, 0x80, bus=5)

        # Resets: 0x4000
        # scd.addResets([
        #     ResetDesc('phy_reset', addr=0x4000, bit=8),
        #     ResetDesc('switch_chip_reset', addr=0x4000, bit=1),
        #     ResetDesc('switch_chip_pcie_reset', addr=0x4000, bit=0),
        # ])

        # scd.addGpios([
        #     GpioDesc("psu1_status", 0x5000, 8, ro=True)
        # ])

        scd.addLeds([
            (0x6040, 'beacon'),
            (0x6050, 'status'),
            (0x6060, 'fan_status'),
            (0x6070, 'psu_status'),
            (0x6080, 'cloud'),
            (0x6090, 'link'),
            (0x60A0, 'poe'),
            (0x60B0, 'speed'),
        ])

        # for psuId in incrange(1, 1):
        #     name = "psu%d" % psuId
        #     scd.newComponent(
        #         PsuSlot,
        #         slotId=psuId,
        #         presentGpio=True,
        #         inputOkGpio=scd.inventory.getGpio("%s_status" % name),
        #         outputOkGpio=scd.inventory.getGpio("%s_status" % name),
        #         led=scd.inventory.getLed(name),

        #     )

        intrRegs = [
            scd.createInterrupt(addr=0x3000, num=0),
        ]

        scd.addEthernetSlotBlock(
            ethernetRange=self.PORTS.ethernetRange
        )

        scd.addSfpSlotBlock(
            sfpRange=self.PORTS.sfpRange,
            addr=0xA010,
            bus=0,
            ledAddr=0x6100,
            intrRegs=intrRegs,
            intrRegIdxFn=lambda xcvrId: 0,
            intrBitFn=lambda xcvrId: 5 + xcvrId - 49
        )

        # self.newComponent(Trident3, PciAddr(bus=1))
