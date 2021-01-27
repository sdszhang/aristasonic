
from . import registerAction
from ....args.show.platform.reboot_cause import rebootCauseParser
from ....show.reboot_cause import ShowRebootCause

@registerAction(rebootCauseParser)
def doShowEnvironment(ctx, args):
   ctx.show.render(ShowRebootCause())
