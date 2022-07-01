from ..core.fixed import FixedChassis, FixedSystem
from ..core.platform import registerPlatform
from ..core.port import PortLayout
from ..core.psu import PsuSlot
from ..core.types import I2cAddr, PciAddr
from ..core.utils import incrange

from ..components.asic.xgs.trident3 import Trident3X2
from ..components.psu.fixed import Fixed100AC
from ..components.scd import Scd, ScdCause
from ..components.vrm import Vrm

from ..descs.gpio import GpioDesc
from ..descs.reset import ResetDesc

from .cpu.prairie import PrairieCpu

class PikeZ1PChassis(FixedChassis):
    FAN_SLOTS = 1
    FAN_COUNT = 2
    PSU_SLOTS = 1

class PikeZ2PChassis(PikeZ1PChassis):
    PSU_SLOTS = 2

class PikeZ(FixedSystem):
    # TODO: Fans

    PORTS = PortLayout(
        ethernets=incrange(1, 48),
        sfps=incrange(49, 52),
    )

    def __init__(self):
        super().__init__()

        self.cpu = self.newComponent(PrairieCpu)
        scd = self.newComponent(Scd, PciAddr(device=0x18, func=7))
        self.scd = scd
        scd.createWatchdog()
        scd.createPowerCycle()
        scd.addSmbusMasterRange(0x8000, 0, 0x80, bus=5)

        scd.addReloadCauseProvider(addr=0x5010, causes=[
            ScdCause(0x00, ScdCause.POWERLOSS),
            ScdCause(0x02, ScdCause.WATCHDOG),
            ScdCause(0x03, ScdCause.REBOOT, 'Button hard reset'),
            ScdCause(0x04, ScdCause.RAIL, 'POS0V8'),
            ScdCause(0x05, ScdCause.RAIL, 'POS1V2'),
            ScdCause(0x06, ScdCause.RAIL, 'POS1V8'),
            ScdCause(0x07, ScdCause.RAIL, 'CPU_SLP_S3'),
            ScdCause(0x08, ScdCause.RAIL, 'POS0V88'),
            ScdCause(0x09, ScdCause.RAIL, 'POS0V8'),
            ScdCause(0x0a, ScdCause.RAIL, 'POS1V8'),
            ScdCause(0x0b, ScdCause.RAIL, 'CPU_3V3'),
            ScdCause(0x0c, ScdCause.REBOOT, 'Button factory reset'),
            ScdCause(0x0d, ScdCause.RAIL, 'APU_VRM'),
            ScdCause(0x0e, ScdCause.OVERTEMP),
            ScdCause(0x0f, ScdCause.REBOOT, 'Software Reboot'),
            ScdCause(0x10, ScdCause.KILLSWITCH),
        ])

        scd.addResets([
            ResetDesc('ext_mux_reset', addr=0x4000, bit=8),
            ResetDesc('phy_reset', addr=0x4000, bit=7),
            ResetDesc('link_flap_reset', addr=0x4000, bit=6),
            ResetDesc('cpu_reset', addr=0x4000, bit=2),
            ResetDesc('switch_chip_reset', addr=0x4000, bit=1, auto=False),
            ResetDesc('switch_chip_pcie_reset', addr=0x4000, bit=0, auto=False),
        ])

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

        for psuId in incrange(1, self.CHASSIS.PSU_SLOTS):
            name = "psu%d" % psuId
            statusGpio = scd.addGpio(
                GpioDesc("%s_status" % name, 0x5000, 7 + psuId, ro=True)
            )
            scd.newComponent(
                PsuSlot,
                slotId=psuId,
                presentGpio=True,
                inputOkGpio=statusGpio,
                outputOkGpio=statusGpio,
                led=scd.inventory.getLed("psu_status"),
                forcePsuLoad=True,
                psus=[
                    Fixed100AC,
                ]
            )

        intrRegs = [
            scd.createInterrupt(addr=0x3000, num=0),
        ]

        scd.addEthernetSlotBlock(
            ethernetRange=self.PORTS.ethernetRange,
            ledAddr=0x6190,
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

        avs = self.newComponent(Vrm, I2cAddr(0, 0x14))

        self.newComponent(Trident3X2, PciAddr(bus=1),
            coreResets=[
                scd.inventory.getReset('switch_chip_reset'),
            ],
            pcieResets=[
                scd.inventory.getReset('switch_chip_pcie_reset'),
            ],
            quirks=[
                Trident3X2.AvsQuirk(avs, Trident3X2.AvsQuirk.TPS549D22),
            ],
        )

@registerPlatform()
class PikeZF(PikeZ):

    CHASSIS = PikeZ1PChassis

    SID = ['PikeIslandZ-F']
    SKU = ['CCS-720DT-48S-F']

@registerPlatform()
class PikeZ2F(PikeZ):

    CHASSIS = PikeZ2PChassis

    SID = ['PikeIslandZ', 'PikeIslandZ-2F']
    SKU = ['CCS-720DT-48S', 'CCS-720DT-48S-2F']

@registerPlatform()
class PikeZR(PikeZ):

    CHASSIS = PikeZ1PChassis

    SID = ['PikeIslandZ-R']
    SKU = ['CCS-720DT-48S-R']

@registerPlatform()
class PikeZ2R(PikeZ):

    CHASSIS = PikeZ2PChassis

    SID = ['PikeIslandZ-2R']
    SKU = ['CCS-720DT-48S-2R']
