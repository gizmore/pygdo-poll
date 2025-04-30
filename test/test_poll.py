import os

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdotest.TestUtil import reinstall_module, text_plug, GDOTestCase, cli_plug, cli_gizmore


class PollTestCase(GDOTestCase):

    def setUp(self):
        super().setUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        Application.init_cli()
        loader = ModuleLoader.instance()
        reinstall_module('poll')
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        loader.init_cli()

    def test_01_cli_poll(self):
        giz = cli_gizmore()
        out = cli_plug(giz, '$poll.add --max-votes=2 "Who is major?" "Peter Lustig" "The other guy" "Third option"')
        self.assertIn('created', out, "Poll was not created.")
        out = cli_plug(giz, '$poll.vote 1 1 2 3')
        self.assertIn('max', out, "Poll max vote values are not checked.")
        out = cli_plug(giz, '$poll.vote 1 1 2')
        self.assertIn('registered', out, "Poll voting does not work.")
        out = cli_plug(giz, "$poll 1")
        self.assertIn('Lustig', out, "Poll show does not work.")
