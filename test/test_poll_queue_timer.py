import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.poll.module_poll import module_poll
from gdo.poll.method.vote_cli import vote_cli


class PollQueueTimerTest(unittest.TestCase):
    def test_active_poll_keeps_queue_unchanged(self):
        module = module_poll()
        with patch('gdo.poll.module_poll.Application.db') as db, \
             patch('gdo.poll.module_poll.GDO_Poll.active_poll', return_value=MagicMock()):
            module.start_next_poll_if_idle()
        db.return_value.query.assert_not_called()
        db.return_value.commit.assert_called_once()

    def test_idle_moves_queue_preserving_durations(self):
        module = module_poll()
        queued = MagicMock()
        queued.gdo_val.return_value = '2026-11-20 20:00:00'
        from gdo.poll.GDO_Poll import GDO_Poll
        with patch('gdo.poll.module_poll.Application.db') as db, \
             patch('gdo.poll.module_poll.Time.get_date', return_value='2026-11-20 19:00:00'), \
             patch('gdo.poll.module_poll.GDO_Poll') as model:
            model.active_poll.return_value = None
            model.utc_timestamp.side_effect = GDO_Poll.utc_timestamp
            model.table.return_value.select.return_value.where.return_value.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = queued
            module.start_next_poll_if_idle()
        query = db.return_value.query.call_args.args[0]
        self.assertIn('poll_starts = DATE_SUB(poll_starts, INTERVAL 3600 SECOND)', query)
        self.assertIn('poll_expires = DATE_SUB(poll_expires, INTERVAL 3600 SECOND)', query)
        db.return_value.commit.assert_called_once()

    def test_vote_uses_requested_trigger(self):
        self.assertEqual('poll', vote_cli.gdo_trigger())


class PollAnnouncementTest(unittest.IsolatedAsyncioTestCase):
    def test_announcement_is_configurable_but_protected(self):
        from gdo.core.GDO_Permission import GDO_Permission
        from gdo.poll.method.announce import announce
        self.assertEqual('poll.announce', announce.gdo_trigger())
        method = announce.__new__(announce)
        self.assertEqual(GDO_Permission.CRONJOB, method.gdo_user_permission())
        self.assertTrue(method.gdo_method_hidden())
        with patch('gdo.base.Application.Application.get_mode', return_value=None):
            self.assertEqual('1', method.gdo_method_config_channel()[0]._initial)

    async def test_announcement_uses_channel_trigger_and_multiple_choice_example(self):
        from gdo.poll.method.announce import announce
        method = announce.__new__(announce)
        poll = MagicMock()
        poll.column.return_value.render_txt.return_value = 'Question'
        poll.is_multiple_choice.return_value = True
        poll.get_choices.return_value = [MagicMock(), MagicMock()]
        poll.get_choices.return_value[0].gdo_val.return_value = 'Yes'
        poll.get_choices.return_value[1].gdo_val.return_value = 'No'
        method.get_poll = MagicMock(return_value=poll)
        method.empty = MagicMock()
        channel = MagicMock()
        channel.get_trigger.return_value = '.'
        channel.get_lang_iso.return_value = 'en'
        channel.send_text = AsyncMock()
        with patch('gdo.poll.method.announce.Application.IS_DOG', True), \
             patch('gdo.poll.method.announce.GDO_Channel.with_setting', return_value=[channel]), \
             patch('gdo.poll.method.announce.GDO_User') as users, \
             patch('gdo.poll.method.announce.Trans'):
            users.table.return_value.with_settings_result.return_value = []
            await method.gdo_execute()
        channel.send_text.assert_awaited_once_with('msg_poll_announce',
                                                  ('Question', '1) Yes, 2) No', '.', '1 2'))
