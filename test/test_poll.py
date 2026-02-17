from gdo.base.Application import Application
import os
from gdo.base.ModuleLoader import ModuleLoader
from gdo.core.connector.Bash import Bash
from gdotest.TestUtil import reinstall_module, text_plug, GDOTestCase, cli_plug, cli_gizmore, all_private_messages
import asyncio

class PollTestCase(GDOTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        Application.init_cli()
        loader = ModuleLoader.instance()
        reinstall_module('poll')
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        loader.init_cli()

    async def test_01_cli_poll(self):
        giz = cli_gizmore()
        chan = Bash.get_server().get_or_create_channel('test_poll')
        out = cli_plug(giz, '$poll.add --max_answers=2 "Who is major?" "Peter Lustig" "The other guy" "Third option"')
        await asyncio.sleep(0.3141)
        out += all_private_messages()
        self.assertIn('New Global Poll', out, "Poll was not announced.")
        self.assertIn('created', out, "Poll was not created.")
        out = cli_plug(giz, '$poll.vote 1 1 2 3')
        self.assertIn('may not enter more than 2', out, "Poll max vote values are not checked.")
        out = cli_plug(giz, '$poll.vote 1 1 2')
        self.assertIn('registered', out, "Poll voting does not work.")
        out = cli_plug(giz, "$poll 1")
        self.assertIn('Lustig', out, "Poll show does not work.")
