import json

import output
from log import logger, RichStdOutputProtocol
import executable
import cmd
from broker import Broker

no_console = output.NoConsole()
sv = executable.Aspect(["before_init", "init", "post_init"])


@sv.actor
class Actor:
    def __init__(self, log):
        self.log = log

    def before_init(self):
        pass
