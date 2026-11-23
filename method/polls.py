from typing import Any
from html import escape
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from gdo.base.Application import Application
from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Render import Mode
from gdo.base.Trans import t
from gdo.base.util.href import href
from gdo.core.GDT_Container import GDT_Container
from gdo.core.GDO_User import GDO_User
from gdo.date.Time import Time
from gdo.date.GDT_Duration import GDT_Duration
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDT_PollOutcome import GDT_PollOutcome
from gdo.table.MethodQueryTable import MethodQueryTable
from gdo.ui.GDT_Link import GDT_Link
from gdo.ui.GDT_Menu import GDT_Menu


class polls(MethodQueryTable):

    @classmethod
    def gdo_trigger(cls) -> str:
        return "polls"

    def gdo_table(self) -> GDO:
        return GDO_Poll.table()

    def gdo_table_headers(self) -> list[GDT]:
        t = self.gdo_table()
        return [
            t.column('poll_id'),
            t.column('poll_title'),
            GDT_PollOutcome('outcome'),
            t.column('poll_created'),
            t.column('poll_expires').copy_as().date_format(Time.FMT_LONG),
        ]
    
    def gdo_execute(self) -> GDT:
        return GDT_Container().vertical().add_fields(
            GDT_Menu().horizontal().add_fields(
                GDT_Link().href(href('poll', 'create')).text('mt_poll_create').icon('add')
            ),
            super().gdo_execute()
        )

    def render_gdo(self, gdo: GDO, mode: Mode) -> Any:
        return f"{gdo.get_id()}-{gdo.gdo_val('poll_title')}"

    def render_poll_expires(self, field: GDT, poll: GDO_Poll) -> str:
        if poll.is_closed():
            return escape(t('poll_countdown_ended'))
        expires = poll.gdo_val('poll_expires')
        if not expires:
            return field.render(Mode.render_cell)
        timestamp = int(GDO_Poll.utc_timestamp(expires))
        ended = t('poll_countdown_ended')
        user = GDO_User.current().get_effective_user()
        zone = user.get_setting_value('timezone')
        if zone:
            try:
                local_zone = ZoneInfo(zone.gdo_val('tz_name'))
            except (ZoneInfoNotFoundError, ValueError):
                local_zone = timezone(zone.get_delta())
        else:
            local_zone = timezone.utc
        local = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(local_zone)
        display = escape(Time.display_datetime_iso(Application.get_lang_iso(), local, Time.FMT_LONG))
        countdown = GDT_Duration('poll_countdown').countdown_until(timestamp, ended).render(Mode.render_html)
        return f'{display} ({countdown})'
