from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.core.GDT_Virtual import GDT_Virtual
from gdo.poll.GDO_Poll import GDO_Poll


class GDO_PollChoice(GDO):

    def gdo_columns(self) -> list[GDT]:
        from gdo.poll.GDO_PollVote import GDO_PollVote
        return [
            GDT_AutoInc('pc_id'),
            GDT_Object('pc_poll').table(GDO_Poll.table()).not_null(),
            GDT_String('pc_text').maxlen(128),
            GDT_Virtual(GDT_UInt('pc_votes')).query(GDO_PollVote.table().select('COUNT(*)').where(f"pv_choice=pc_id")),
        ]
