from typing import Any

from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Render import Mode
from gdo.base.util.href import href
from gdo.core.GDT_Container import GDT_Container
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
            t.column('poll_title'),
            GDT_PollOutcome('outcome'),
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
