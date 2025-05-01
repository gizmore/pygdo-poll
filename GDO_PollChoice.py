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
            GDT_Object('pc_poll').table(GDO_Poll.table()).not_null().cascade_delete(),
            GDT_String('pc_text').maxlen(128),
        ]

    def render_title(self) -> str:
        return self.gdo_val('pc_text')

    def render_percent(self) -> str:
        total = int(self._vals['total_votes'])
        if not total:
            return '?,??%'
        return str(round(int(self._vals['num_votes']) / total * 100, 1)) + '%'
