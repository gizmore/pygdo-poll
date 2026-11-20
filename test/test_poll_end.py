import unittest
from unittest.mock import MagicMock, patch

from gdo.core.GDO_Permission import GDO_Permission
from gdo.poll.method.end import end


class PollEndTest(unittest.IsolatedAsyncioTestCase):
    def method(self, force):
        method = end.__new__(end)
        method.param_value = MagicMock(return_value=force)
        method.err = MagicMock(side_effect=lambda key: key)
        method.reply = MagicMock(return_value='ended')
        return method

    async def test_admin_and_force_required(self):
        method = self.method(False)
        self.assertEqual(GDO_Permission.ADMIN, method.gdo_user_permission())
        with patch('gdo.poll.method.end.Application.db') as db:
            self.assertEqual('err_poll_end_force', await method.gdo_execute())
            db.assert_not_called()

    async def test_no_active_poll(self):
        method = self.method(True)
        with patch('gdo.poll.method.end.Application.db'), \
             patch('gdo.poll.method.end.GDO_Poll.active_poll', return_value=None):
            self.assertEqual('err_poll_no_active', await method.gdo_execute())

    async def test_ends_only_current_poll(self):
        method = self.method(True)
        poll = MagicMock()
        poll.render_title.return_value = 'Current'
        with patch('gdo.poll.method.end.Application.db') as db, \
             patch('gdo.poll.method.end.GDO_Poll.active_poll', return_value=poll), \
             patch('gdo.poll.method.end.module_poll') as module, \
             patch('gdo.poll.method.end.Time.get_date', return_value='2026-11-20 18:00:00'):
            self.assertEqual('ended', await method.gdo_execute())
        db.return_value.select.assert_called_once()
        poll.save_val.assert_called_once_with('poll_closed', '2026-11-20 18:00:00')
        module.instance.return_value.get_sidebar_polls.cache_clear.assert_called_once()
        method.reply.assert_called_once_with('msg_poll_ended', ('Current',))
