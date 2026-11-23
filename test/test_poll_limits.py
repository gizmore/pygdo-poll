import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.poll.method.create import create
from gdo.poll.method.vote import vote


class PollLimitTest(unittest.IsolatedAsyncioTestCase):
    async def test_revote_replaces_previous_choices(self):
        method = vote.__new__(vote)
        method._env_user = MagicMock()
        method._env_user.get_id.return_value = '42'
        poll = MagicMock()
        poll.get_id.return_value = '9'
        poll.is_closed.return_value = False
        poll.is_active.return_value = True
        poll.get_min_choices.return_value = 1
        poll.get_max_choices.return_value = 2
        method.get_poll = MagicMock(return_value=poll)
        method.clear_form = MagicMock()
        method.msg = MagicMock(return_value='voted')
        old_votes = [MagicMock(), MagicMock()]
        new_choice = MagicMock()
        new_choice.get_id.return_value = '7'
        with patch('gdo.poll.method.vote.GDO_PollVote') as model, \
             patch('gdo.poll.method.vote.Application.EVENTS', create=True) as events:
            model.table.return_value.select.return_value.join_object.return_value.where.return_value.exec.return_value = old_votes
            events.publish = AsyncMock()
            self.assertEqual('voted', await method.chosen_submitted([new_choice]))
        for old in old_votes:
            old.delete.assert_called_once()
        model.blank.assert_called_once_with({'pv_user': '42', 'pv_choice': '7'})
        model.blank.return_value.insert.assert_called_once()

    async def test_closed_poll_revote_preserves_previous_vote(self):
        method = vote.__new__(vote)
        method._env_user = MagicMock()
        method.get_poll = MagicMock()
        method.get_poll.return_value.is_closed.return_value = True
        method.err = MagicMock(return_value='closed')
        with patch('gdo.poll.method.vote.GDO_PollVote') as model:
            self.assertEqual('closed', await method.chosen_submitted([MagicMock()]))
        method.err.assert_called_once_with('err_poll_closed')
        model.table.assert_not_called()
        model.blank.assert_not_called()

    async def test_create_persists_minimum(self):
        method = create.__new__(create)
        method.param_value = MagicMock(side_effect=lambda key: {
            'choices': ['One', 'Two', 'Three'], 'min_answers': 2, 'max_answers': 3, 'duration_days': 2,
        }[key])
        method.param_val = MagicMock(side_effect=lambda key: {
            'title': 'Question', 'question': 'Details', 'min_answers': '2', 'max_answers': '3',
        }[key])
        method.clear_form = MagicMock()
        method.msg = MagicMock()
        poll = MagicMock()
        with patch('gdo.poll.method.create.GDO_Poll') as model, \
             patch('gdo.poll.method.create.GDO_PollChoice'), \
             patch('gdo.poll.method.create.module_poll') as module, \
             patch('gdo.poll.method.create.Application.db') as db, \
             patch('gdo.poll.method.create.GDT_Redirect') as redirect, \
             patch('gdo.poll.method.create.href', return_value='/vote'):
            model.blank.return_value.insert.return_value = poll
            model.table.return_value.select.return_value.where.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            model.table.return_value.select.return_value.where.return_value.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            module.instance.return_value.get_config_value.return_value = 0
            redirect.return_value.href.return_value = redirect.return_value
            await method.form_submitted()
        self.assertEqual('2', model.blank.call_args.args[0]['poll_min_answers'])
        self.assertEqual('3', model.blank.call_args.args[0]['poll_max_answers'])
        self.assertIsNotNone(model.blank.call_args.args[0]['poll_starts'])
        self.assertIsNotNone(model.blank.call_args.args[0]['poll_expires'])
        module.instance.return_value.get_sidebar_polls.cache_clear.assert_called_once()

    async def test_invalid_bounds_do_not_create_poll(self):
        for minimum, maximum in ((3, 2), (1, 4)):
            method = create.__new__(create)
            method.param_value = MagicMock(side_effect=lambda key: {
                'choices': ['One', 'Two', 'Three'], 'min_answers': minimum, 'max_answers': maximum,
            }[key])
            method.err = MagicMock(return_value='invalid')
            with patch('gdo.poll.method.create.GDO_Poll') as model:
                self.assertEqual('invalid', await method.form_submitted())
                model.blank.assert_not_called()

    async def test_duplicate_choices_do_not_replace_existing_votes(self):
        method = vote.__new__(vote)
        method._env_user = MagicMock()
        method.get_poll = MagicMock()
        method.get_poll.return_value.is_closed.return_value = False
        method.err = MagicMock(return_value='invalid')
        choice = MagicMock()
        choice.get_id.return_value = '7'
        with patch('gdo.poll.method.vote.GDO_PollVote') as model:
            self.assertEqual('invalid', await method.chosen_submitted([choice, choice]))
            method.err.assert_called_once_with('err_poll_duplicate_choice')
            model.table.assert_not_called()

    async def test_future_poll_cannot_receive_votes(self):
        method = vote.__new__(vote)
        method._env_user = MagicMock()
        method.get_poll = MagicMock()
        method.get_poll.return_value.is_closed.return_value = False
        method.get_poll.return_value.is_active.return_value = False
        method.err = MagicMock(return_value='not started')
        with patch('gdo.poll.method.vote.GDO_PollVote') as model:
            self.assertEqual('not started', await method.chosen_submitted([MagicMock()]))
            method.err.assert_called_once_with('err_poll_not_started')
            model.table.assert_not_called()

    async def test_text_vote_selects_active_poll_without_id(self):
        from gdo.poll.method.vote_cli import vote_cli
        method = vote_cli.__new__(vote_cli)
        poll = MagicMock()
        with patch('gdo.poll.method.vote_cli.GDO_Poll.active_poll', return_value=poll):
            self.assertEqual([], method.gdo_parameters())
            self.assertIs(poll, method.get_poll())

    async def test_insufficient_credits_do_not_create_poll(self):
        method = create.__new__(create)
        method._env_user = MagicMock()
        method._env_user.get_id.return_value = '42'
        method.param_value = MagicMock(side_effect=lambda key: {
            'choices': ['One', 'Two'], 'min_answers': 1, 'max_answers': 1, 'duration_days': 3,
        }[key])
        method.err = MagicMock(return_value='insufficient')
        with patch('gdo.poll.method.create.GDO_Poll') as model, \
             patch('gdo.poll.method.create.module_poll') as module, \
             patch('gdo.poll.method.create.Application.db') as db, \
             patch('gdo.poll.method.create.module_enabled', return_value=True), \
             patch('gdo.core.GDO_UserSetting.GDO_UserSetting.quote', return_value="'42'"):
            query = model.table.return_value.select.return_value.where.return_value
            query.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            query.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            module.instance.return_value.get_config_value.return_value = 5
            db.return_value.query.return_value.rowcount = 0
            self.assertEqual('insufficient', await method.form_submitted())
            method.err.assert_called_once_with('err_poll_insufficient_credits', (15,))
            model.blank.assert_not_called()

    async def test_paid_poll_debits_total_before_creation(self):
        method = create.__new__(create)
        method._env_user = MagicMock()
        method._env_user.get_id.return_value = '42'
        method.param_value = MagicMock(side_effect=lambda key: {
            'choices': ['One', 'Two'], 'min_answers': 1, 'max_answers': 1, 'duration_days': 3,
        }[key])
        method.param_val = MagicMock(side_effect=lambda key: {
            'title': 'Paid', 'question': '', 'min_answers': '1', 'max_answers': '1',
        }[key])
        method.clear_form = MagicMock()
        method.msg = MagicMock()
        with patch('gdo.poll.method.create.GDO_Poll') as model, \
             patch('gdo.poll.method.create.GDO_PollChoice'), \
             patch('gdo.poll.method.create.module_poll') as module, \
             patch('gdo.poll.method.create.Application.db') as db, \
             patch('gdo.poll.method.create.module_enabled', return_value=True), \
             patch('gdo.core.GDO_UserSetting.GDO_UserSetting.quote', return_value="'42'"), \
             patch('gdo.poll.method.create.GDT_Redirect') as redirect, \
             patch('gdo.poll.method.create.href', return_value='/vote'):
            query = model.table.return_value.select.return_value.where.return_value
            query.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            query.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            module.instance.return_value.get_config_value.return_value = 5
            db.return_value.query.return_value.rowcount = 1
            redirect.return_value.href.return_value = redirect.return_value
            await method.form_submitted()
            self.assertIn('>= 15', db.return_value.query.call_args.args[0])
            model.blank.assert_called_once()
            self.assertTrue(method._credits_charged)

    async def test_queued_poll_starts_after_prior_poll_expires(self):
        from gdo.base.Application import Application
        from gdo.date.Time import Time
        from gdo.poll.GDO_Poll import GDO_Poll
        method = create.__new__(create)
        method.param_value = MagicMock(side_effect=lambda key: {
            'choices': ['One', 'Two'], 'min_answers': 1, 'max_answers': 1, 'duration_days': 2,
        }[key])
        method.param_val = MagicMock(side_effect=lambda key: {
            'title': 'Next', 'question': '', 'min_answers': '1', 'max_answers': '1',
        }[key])
        method.clear_form = MagicMock()
        method.msg = MagicMock()
        last = MagicMock()
        last.gdo_val.return_value = Time.get_date(Application.TIME + Time.ONE_DAY)
        with patch('gdo.poll.method.create.GDO_Poll') as model, \
             patch('gdo.poll.method.create.GDO_PollChoice'), \
             patch('gdo.poll.method.create.module_poll') as module, \
             patch('gdo.poll.method.create.Application.db'), \
             patch('gdo.poll.method.create.GDT_Redirect') as redirect, \
             patch('gdo.poll.method.create.href', return_value='/show'):
            query = model.table.return_value.select.return_value.where.return_value
            query.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            query.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = last
            model.utc_timestamp.side_effect = GDO_Poll.utc_timestamp
            module.instance.return_value.get_config_value.return_value = 0
            redirect.return_value.href.return_value = redirect.return_value
            await method.form_submitted()
        inserted = model.blank.call_args.args[0]
        self.assertEqual(last.gdo_val.return_value, inserted['poll_starts'])
        self.assertAlmostEqual(2 * Time.ONE_DAY,
                               Time.get_time(inserted['poll_expires']) - Time.get_time(inserted['poll_starts']), delta=1)
        self.assertFalse(method._announce_now)

    def test_outcomes_render_html_and_text_for_connectors(self):
        from gdo.poll.GDT_PollOutcome import GDT_PollOutcome
        poll = MagicMock()
        poll.get_id.return_value = '1'
        poll.is_closed.return_value = True
        choice = MagicMock()
        choice.render_title.return_value = '<Option>'
        choice.render_percent.return_value = '50%'
        poll.get_choices.return_value = [choice]
        with patch('gdo.core.GDT_String.t', side_effect=lambda key, *args: key), \
             patch('gdo.ui.WithIcon.t', side_effect=lambda key, *args: key), \
             patch('gdo.poll.GDT_PollOutcome.t', side_effect=lambda key, args: '%s) %s (%s)' % args):
            outcome = GDT_PollOutcome('outcome').poll(poll)
            self.assertIn('&lt;Option&gt;', outcome.render_card())
            self.assertEqual('1) <Option> (50%)', outcome.render_irc())

    def test_results_hidden_for_open_and_queued_polls_in_all_modes(self):
        from gdo.poll.GDT_PollOutcome import GDT_PollOutcome
        poll = MagicMock()
        poll.get_id.return_value = '1'
        poll.is_closed.return_value = False
        with patch('gdo.core.GDT_String.t', side_effect=lambda key, *args: key), \
             patch('gdo.ui.WithIcon.t', side_effect=lambda key, *args: key), \
             patch('gdo.poll.GDT_PollOutcome.t', return_value='Hidden'):
            outcome = GDT_PollOutcome('outcome').poll(poll)
            for render in (outcome.render_html, outcome.render_cell, outcome.render_card,
                           outcome.render_txt, outcome.render_irc, outcome.render_json):
                self.assertEqual('Hidden', render())
        poll.get_choices.assert_not_called()

    def test_poll_overview_includes_full_expiry_timestamp(self):
        from gdo.date.GDT_Timestamp import GDT_Timestamp
        from gdo.date.Time import Time
        from gdo.poll.method.polls import polls
        with patch('gdo.ui.WithIcon.t', side_effect=lambda key: key):
            expiry = GDT_Timestamp('poll_expires')
            table = MagicMock()
            table.column.side_effect = lambda name: expiry if name == 'poll_expires' else MagicMock()
            method = polls.__new__(polls)
            method.gdo_table = MagicMock(return_value=table)
            headers = method.gdo_table_headers()
        self.assertEqual('poll_expires', headers[-1].get_name())
        self.assertEqual(Time.FMT_LONG, headers[-1]._date_format)
        self.assertNotEqual(Time.FMT_LONG, expiry._date_format)

    def test_poll_overview_adds_countdown_and_respects_early_close(self):
        from gdo.poll.method.polls import polls
        method = polls.__new__(polls)
        field = MagicMock()
        field.render.return_value = '23 Nov 2026'
        poll = MagicMock()
        poll.is_closed.return_value = False
        poll.gdo_val.return_value = '2026-11-23 12:00:00'
        zone = MagicMock()
        zone.gdo_val.return_value = 'Europe/Berlin'
        with patch('gdo.poll.method.polls.t', return_value='Ended'), \
             patch('gdo.poll.method.polls.GDO_User.current') as current, \
             patch('gdo.poll.method.polls.Application.get_lang_iso', return_value='en'), \
             patch('gdo.base.Application.Application.get_mode', return_value=None), \
             patch('gdo.date.GDT_Duration.Time.human_duration', return_value='2h'), \
             patch('gdo.poll.method.polls.Time.display_datetime_iso', return_value='23 Nov 2026') as display:
            current.return_value.get_effective_user.return_value.get_setting_value.return_value = zone
            result = method.render_poll_expires(field, poll)
            self.assertIn('23 Nov 2026', result)
            self.assertEqual(13, display.call_args.args[1].hour)
            self.assertIn('class="gdt-duration-countdown"', result)
            self.assertIn('data-countdown-until=', result)
            poll.is_closed.return_value = True
            self.assertEqual('Ended', method.render_poll_expires(field, poll))

    async def test_failed_announcement_is_not_marked_as_sent(self):
        from gdo.poll.module_poll import module_poll
        module = module_poll()
        poll = MagicMock()
        with patch('gdo.poll.module_poll.Application.IS_DOG', True), \
             patch.object(module, 'start_next_poll_if_idle'), \
             patch.object(module, 'announce_ended_polls', new_callable=AsyncMock), \
             patch('gdo.poll.module_poll.GDO_Poll') as model, \
             patch('gdo.base.IPC.IPC.execute_dog_event', new_callable=AsyncMock,
                   side_effect=RuntimeError('delivery failed')):
            model.table.return_value.select.return_value.where.return_value.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = poll
            with self.assertRaisesRegex(RuntimeError, 'delivery failed'):
                await module.announce_active_poll()
        poll.save_val.assert_not_called()


if __name__ == '__main__':
    unittest.main()
