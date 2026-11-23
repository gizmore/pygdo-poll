from functools import lru_cache

from gdo.base.Application import Application
from gdo.base.Cache import gdo_redis_cached, gdo_lru_cache
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Container import GDT_Container
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Duration import GDT_Duration
from gdo.date.Time import Time
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDO_PollChoice import GDO_PollChoice
from gdo.poll.GDO_PollVote import GDO_PollVote
from gdo.ui.GDT_Link import GDT_Link
from gdo.ui.GDT_Page import GDT_Page
from gdo.base.GDO import GDO


class module_poll(GDO_Module):

    def gdo_classes(self) -> list[type[GDO]]:
        return [
            GDO_Poll,
            GDO_PollChoice,
            GDO_PollVote,
        ]

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_Bool('email_new_polls').not_null().initial('1'),
            GDT_Bool('email_all_users').not_null().initial('0'),
            GDT_UInt('max_side_polls').not_null().initial('3'),
            GDT_Duration('max_age_side_polls').not_null().initial('1w'),
            GDT_UInt('poll_credits_per_day').not_null().initial('0'),
        ]

    def cfg_email_new_polls(self) -> bool:
        return self.get_config_value('email_new_polls')

    def cfg_email_all_users(self) -> bool:
        return self.get_config_value('email_all_users')

    def cfg_max_side_polls(self) -> int:
        return self.get_config_value('max_side_polls')

    def cfg_max_age_side_polls(self) -> int:
        return self.get_config_value('max_age_side_polls')

    def gdo_user_config(self) -> list[GDT]:
        return [
            GDT_UInt('effective_poll_vote_power').initial('0'),
        ]

    def gdo_user_settings(self) -> list[GDT]:
        return [
            GDT_Bool('email_polls').not_null().initial('1'),
            GDT_Bool('msg_polls').not_null().initial('0'),
        ]

    def gdo_load_scripts(self, page: 'GDT_Page'):
        self.add_js('js/pygdo-poll.js')
        self.add_css('css/pygdo-poll.css')

    def gdo_subscribe_events(self):
        Application.EVENTS.add_timer_async(10, self.announce_active_poll, Application.EVENTS.FOREVER)

    async def announce_active_poll(self):
        if not Application.IS_DOG:
            return
        await self.announce_ended_polls()
        self.start_next_poll_if_idle()
        now = Time.get_date()
        poll = (GDO_Poll.table().select().where(
            f"poll_broadcasted IS NULL AND poll_starts <= '{now}' "
            f"AND poll_expires > '{now}' AND poll_closed IS NULL")
                .order('poll_starts ASC').first().nocache().exec().fetch_object())
        if poll:
            from gdo.base.IPC import IPC
            await IPC.execute_dog_event('poll.announce', (poll.get_id(),))
            poll.save_val('poll_broadcasted', now)

    async def announce_ended_polls(self):
        """Claim end notices once before sending, avoiding repeated floods."""
        from gdo.base.IPC import IPC
        now = Time.get_date()
        poll = (GDO_Poll.table().select().where(
            f"poll_end_pending=1 AND (poll_closed IS NOT NULL OR poll_expires <= '{now}')")
                .order('poll_id ASC').first().nocache().exec().fetch_object())
        if not poll:
            return
        poll_id = int(poll.get_id())
        result = Application.db().query(
            f'UPDATE gdo_poll SET poll_end_pending=0 WHERE poll_id={poll_id} AND poll_end_pending=1')
        if result.rowcount == 1:
            await IPC.execute_dog_event('poll.announce_end', (str(poll_id),))

    def start_next_poll_if_idle(self):
        """Move the waiting schedule forward when no poll is currently active."""
        db = Application.db()
        db.begin()
        try:
            db.select("SELECT module_id FROM gdo_module WHERE module_name = 'poll' FOR UPDATE").fetch_row()
            if GDO_Poll.active_poll():
                db.commit()
                return
            now = Time.get_date()
            next_poll = (GDO_Poll.table().select().where(
                f"poll_closed IS NULL AND poll_starts > '{now}' AND poll_expires IS NOT NULL")
                .order('poll_starts ASC, poll_id ASC').first().nocache().exec().fetch_object())
            if next_poll:
                starts = next_poll.gdo_val('poll_starts')
                delta = int(GDO_Poll.utc_timestamp(starts) - GDO_Poll.utc_timestamp(now))
                # Move the entire remaining queue together, keeping paid durations and ordering.
                db.query("UPDATE gdo_poll SET "
                         f"poll_starts = DATE_SUB(poll_starts, INTERVAL {delta} SECOND), "
                         f"poll_expires = DATE_SUB(poll_expires, INTERVAL {delta} SECOND) "
                         f"WHERE poll_closed IS NULL AND poll_starts >= '{starts}' "
                         "AND poll_expires IS NOT NULL")
                self.get_sidebar_polls.cache_clear()
            db.commit()
        except Exception:
            db.rollback()
            raise

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        self.add_sidebar_polls(page)

    def add_sidebar_polls(self, page):
        page._right_bar.add_field(GDT_Link().href(self.href('polls')).text('polls').icon('vote'))
        polls = self.get_sidebar_polls()
        page._right_bar.add_field(polls)

    @gdo_lru_cache
    def get_sidebar_polls(self) -> GDT:
        cont = GDT_Container().vertical()
        cut = Time.get_date(Application.TIME - self.cfg_max_age_side_polls())
        result = (GDO_Poll.table().select().
                  order('poll_created DESC').
                  limit(self.cfg_max_side_polls()).
                  where(f"poll_created >= '{cut}'").
                  nocache().exec())
        for poll in result:
            cont.add_field(
                GDT_Link().href(self.href('show', f"&poll={poll.get_id()}")).
                text('poll_sidebar_title', (poll.gdo_val('poll_title'),)))
        return cont
