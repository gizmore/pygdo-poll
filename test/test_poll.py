from gdo.base.Application import Application
from gdo.base.IPC import IPC
import os
from gdo.base.ModuleLoader import ModuleLoader
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.module_poll import module_poll
from gdo.date.Time import Time
from gdo.core.connector.Bash import Bash
from gdotest.TestUtil import reinstall_module, text_plug, GDOTestCase, cli_plug, cli_gizmore, all_private_messages, install_module, web_plug
import asyncio
from unittest.mock import AsyncMock, patch

class PollTestCase(GDOTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        Application.init_cli()
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        install_module('poll')
        loader.init_modules(True, True)
        loader.init_cli()

    async def test_00_reinstall(self):
        reinstall_module('poll')

    async def test_01_cli_poll(self):
        giz = cli_gizmore()
        chan = Bash.get_server().get_or_create_channel('test_poll')
        out = cli_plug(giz, '$poll.add --max_answers=2 "Who is major?" "Peter Lustig" "The other guy" "Third option"')
        await IPC.execute_dog_event('poll.announce', ('1',))
        await asyncio.sleep(0.3141)
        out += all_private_messages()
        self.assertIn('New Global Poll', out, "Poll was not announced.")
        self.assertIn('created', out, "Poll was not created.")
        out = cli_plug(giz, '$poll.vote 1 2 3')
        self.assertIn('may not enter more than 2', out, "Poll max vote values are not checked.")
        out = cli_plug(giz, '$poll.vote 1 2')
        self.assertIn('registered', out, "Poll voting does not work.")
        out = cli_plug(giz, "$poll 1")
        self.assertIn('Lustig', out, "Poll show does not work.")

    async def test_02_paid_queue(self):
        reinstall_module('poll')
        install_module('payment_credits')
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        loader.init_cli()
        giz = cli_gizmore()
        giz.save_setting('credits', '100')
        await module_poll.instance().save_config_val('poll_credits_per_day', '5')
        out = cli_plug(giz, '$poll.add --duration_days=2 "First?" "Yes" "No"')
        self.assertIn('created', out)
        out = cli_plug(giz, '$poll.add --duration_days=3 "Second?" "Yes" "No"')
        self.assertIn('queued', out)
        polls = list(GDO_Poll.table().select().order('poll_id ASC').nocache().exec())
        self.assertEqual(2, len(polls))
        self.assertEqual(polls[0].gdo_val('poll_expires'), polls[1].gdo_val('poll_starts'))
        self.assertAlmostEqual(3 * Time.ONE_DAY, GDO_Poll.utc_timestamp(polls[1].gdo_val('poll_expires')) - GDO_Poll.utc_timestamp(polls[1].gdo_val('poll_starts')), delta=1)
        self.assertEqual(75, int(giz.get_setting_val('credits')))
        self.assertTrue(polls[0].is_active())
        self.assertFalse(polls[1].is_active())
        out = cli_plug(giz, '$poll.add --duration_days=30 "Too expensive?" "Yes" "No"')
        self.assertIn('requires 150 credits', out)
        self.assertEqual(75, int(giz.get_setting_val('credits')))
        self.assertEqual(2, GDO_Poll.table().count_where())
        previous_time, previous_dog = Application.TIME, Application.IS_DOG
        try:
            Application.TIME = GDO_Poll.utc_timestamp(polls[1].gdo_val('poll_starts')) + 1
            Application.IS_DOG = True
            with patch.object(IPC, 'execute_dog_event', new_callable=AsyncMock) as announce:
                await module_poll.instance().announce_active_poll()
                announce.assert_awaited_once_with('poll.announce', (polls[1].get_id(),))
                await module_poll.instance().announce_active_poll()
                announce.assert_awaited_once()
        finally:
            Application.TIME, Application.IS_DOG = previous_time, previous_dog

    async def test_03_http_poll_pages(self):
        poll = GDO_Poll.active_poll()
        request = web_plug(f'poll.show.html?poll={poll.get_id()}').user('gizmore')
        request.COOKIES[Application.config('sess.name', 'GDO')] = request.COOKIES.pop('GDO')
        page = request.exec()
        self.assertIn('poll-outcome', page)
        self.assertIn('First?', page)
        request = web_plug(f'poll.vote.html?poll={poll.get_id()}').user('gizmore')
        request.COOKIES[Application.config('sess.name', 'GDO')] = request.COOKIES.pop('GDO')
        page = request.exec()
        self.assertIn('pc1', page)
        self.assertIn('pc2', page)
        request = web_plug(f'poll.vote.html?poll={poll.get_id()}').user('gizmore')
        request.COOKIES[Application.config('sess.name', 'GDO')] = request.COOKIES.pop('GDO')
        page = request.post({'pc1': '1', 'submit': '1'}).exec()
        self.assertIn('Your vote has been registered', page)
