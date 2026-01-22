from typing import Any

from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Render import Mode
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDT_PollOutcome import GDT_PollOutcome
from gdo.table.MethodQueryTable import MethodQueryTable


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

    def render_gdo(self, gdo: GDO, mode: Mode) -> Any:
        return f"{gdo.get_id()}-{gdo.gdo_val('poll_title')}"
