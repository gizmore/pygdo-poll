import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.poll.module_poll import module_poll
from gdo.poll.method.announce_end import announce_end
from gdo.poll.method.mail import mail


class EndAnnouncementTest(unittest.IsolatedAsyncioTestCase):
    async def test_end_notice_claims_before_delivery_and_only_once(self):
        module = module_poll()
        poll = MagicMock()
        poll.get_id.return_value = '42'
        with patch('gdo.poll.module_poll.GDO_Poll') as model, \
             patch('gdo.poll.module_poll.Time.get_date', return_value='2026-11-23 12:00:00'), \
             patch('gdo.poll.module_poll.Application.db') as db, \
             patch('gdo.base.IPC.IPC.execute_dog_event', new_callable=AsyncMock) as send:
            model.table.return_value.select.return_value.where.return_value.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = poll
            db.return_value.query.return_value.rowcount = 1
            await module.announce_ended_polls()
            db.return_value.query.return_value.rowcount = 0
            await module.announce_ended_polls()
        send.assert_awaited_once_with('poll.announce_end', ('42',))
        self.assertIn('poll_end_pending=1', db.return_value.query.call_args.args[0])

    async def test_end_notice_continues_after_send_failure(self):
        method = announce_end.__new__(announce_end)
        poll = MagicMock()
        poll.is_closed.return_value = True
        poll.render_title.return_value = 'Question'
        choice = MagicMock()
        choice.render_title.return_value = 'Yes'
        choice._vals = {'num_votes': '3'}
        poll.get_choices.return_value = [choice]
        method.param_value = MagicMock(return_value=poll)
        method.empty = MagicMock()
        channels = [MagicMock(), MagicMock()]
        for channel in channels:
            channel.send_text = AsyncMock()
        channels[0].send_text.side_effect = RuntimeError('secret token')
        with patch('gdo.poll.method.announce_end.Application.IS_DOG', True), \
             patch('gdo.poll.method.announce_end.announce'), \
             patch('gdo.poll.method.announce_end.GDO_Channel.with_setting', return_value=channels), \
             patch('gdo.poll.method.announce_end.GDO_User') as users, \
             patch('gdo.poll.method.announce_end.Trans'), \
             patch('gdo.poll.method.announce_end.Logger.error') as log, \
             patch('gdo.poll.method.mail.mail') as mailer:
            users.table.return_value.with_settings_result.return_value = []
            await method.gdo_execute()
        channels[1].send_text.assert_awaited_once_with('msg_poll_end_announce', ('Question', 'Yes: 3'))
        self.assertNotIn('secret token', str(log.call_args_list))
        mailer.return_value.mail_results.assert_called_once_with(poll, 'Yes: 3')

    def test_new_poll_mail_failure_does_not_skip_other_users(self):
        sender = mail.__new__(mail)
        sender.get_users = MagicMock(return_value=['first', 'second'])
        sender.mail_poll_to_user = MagicMock(side_effect=[RuntimeError('secret'), None])
        with patch('gdo.poll.method.mail.Logger.error') as log:
            sender.mail_poll(MagicMock())
        self.assertEqual(2, sender.mail_poll_to_user.call_count)
        self.assertNotIn('secret', str(log.call_args_list))

    def test_new_poll_mail_uses_clickable_choice_links(self):
        sender = mail.__new__(mail)
        poll = MagicMock()
        poll.is_multiple_choice.return_value = False
        choice = MagicMock()
        choice.render_title.return_value = 'Yes'
        link = MagicMock()
        link.href.return_value = link
        link.text_raw.return_value = link
        link.render_html.return_value = '<a>Yes</a>'
        with patch('gdo.poll.method.mail.vote') as vote_method, \
             patch('gdo.poll.method.mail.GDT_Link', return_value=link), \
             patch('gdo.poll.method.mail.url', return_value='/vote'), \
             patch('gdo.poll.method.mail.t', return_value='message'), \
             patch('gdo.poll.method.mail.sitename', return_value='site'), \
             patch('gdo.poll.method.mail.Mail') as mail_model:
            vote_method.return_value.create_autologin_token.return_value = 'token'
            sender.send_mail_to_user(poll, [choice], MagicMock())
        link.text_raw.assert_called_once_with('Yes')
        link.render_html.assert_called_once()
        mail_model.from_bot.return_value.send_to_user.assert_called_once()
