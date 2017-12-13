# See readme.md for instructions on running this code.
import logging
from six.moves.urllib import parse
from zulip_bots.bots.dialogflow_welcome.welcome_handler import WelcomeHandler
from zulip_bots.bots.dialogflow.dialogflow import DialogFlowHandler
import json

import apiai

from typing import Any

class DialogFlowWelcomeHandler(DialogFlowHandler):
    def initialize(self, bot_handler: Any):
        super(DialogFlowWelcomeHandler, self).initialize(bot_handler)
        WelcomeHandler(bot_handler._client)

handler_class = DialogFlowWelcomeHandler
