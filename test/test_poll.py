import os

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdotest.TestUtil import reinstall_module, text_plug, GDOTestCase, cli_plug, cli_gizmore


class PollTestCase(GDOTestCase):

    def setUp(self):
        super().setUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        reinstall_module('poll')
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        loader.init_cli()

    def test_01_cli_poll(self):
        giz = cli_gizmore()
        out = cli_plug(giz, '$poll "Who is major?" "" ')
        self.assertIn('created', out, "Poll was not created.")
