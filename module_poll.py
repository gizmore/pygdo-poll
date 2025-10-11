import functools

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.util.href import href
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


class module_poll(GDO_Module):

    def gdo_classes(self):
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
        ]

    def cfg_email_new_polls(self) -> bool:
        return self.get_config_value('email_new_polls')

    def cfg_email_all_users(self) -> bool:
        return self.get_config_value('email_all_users')

    def cfg_max_side_polls(self) -> int:
        return self.get_config_value('max_side_polls')

    def cfg_max_age_side_polls(self) -> int:
        return self.get_config_value('max_age_side_polls')

    def gdo_user_settings(self) -> list[GDT]:
        return [
            GDT_Bool('email_new_polls').not_null().initial('0'),
        ]

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        page._right_bar.add_field(
            GDT_Link().href(href('poll', 'create')).text('mt_poll_create'),
        )
        self.add_sidebar_polls(page)

    def add_sidebar_polls(self, page):
        polls = self.get_sidebar_polls()
        page._right_bar.add_field(polls)

    @functools.cache
    def get_sidebar_polls(self) -> GDT:
        cont = GDT_Container()
        cut = Time.get_date(Application.TIME - self.cfg_max_age_side_polls())
        result = (GDO_Poll.table().select().
                  select('(SELECT COUNT(*) FROM gdo_pollvote LEFT JOIN gdo_pollchoice ON pv_choice=pc_id WHERE pc_poll=poll_id) AS votecount').
                  order('poll_created DESC').
                  limit(self.cfg_max_side_polls()).
                  where(f"poll_created >= '{cut}'").
                  nocache().exec())
        for poll in result:
            cont.add_field(
                GDT_Link().href(self.href('show', f"&poll={poll.get_id()}")).
                text('poll_sidebar', (poll.gdo_val('poll_title'), poll._vals['votecount'])))
        return cont
