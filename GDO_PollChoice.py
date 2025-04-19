from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_String import GDT_String
from gdo.poll.GDO_Poll import GDO_Poll


class GDO_PollChoice(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('pc_id'),
            GDT_Object('pc_poll').table(GDO_Poll.table()).not_null(),
            GDT_String('pc_text').maxlen(128),
        ]
