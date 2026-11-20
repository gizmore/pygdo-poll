from gdo.base.Application import Application
from gdo.base.Method import Method
from gdo.core.Connector import Connector
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.date.Time import Time
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.module_poll import module_poll


class end(Method):
    @classmethod
    def gdo_trigger(cls) -> str:
        return 'poll.end'

    def gdo_connectors(self) -> str:
        return Connector.text_connectors()

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.ADMIN

    def gdo_transactional(self) -> bool:
        return True

    def gdo_parameters(self):
        return [GDT_Bool('force').not_null().initial('0')]

    async def gdo_execute(self):
        if not self.param_value('force'):
            return self.err('err_poll_end_force')
        # Share the schedule lock with poll creation; never close a queued poll.
        Application.db().select("SELECT module_id FROM gdo_module WHERE module_name = 'poll' FOR UPDATE").fetch_row()
        poll = GDO_Poll.active_poll()
        if not poll:
            return self.err('err_poll_no_active')
        poll.save_val('poll_closed', Time.get_date())
        module_poll.instance().get_sidebar_polls.cache_clear()
        return self.reply('msg_poll_ended', (poll.render_title(),))
