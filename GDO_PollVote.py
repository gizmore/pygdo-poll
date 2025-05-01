from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_User import GDT_User
from gdo.date.GDT_Created import GDT_Created
from gdo.poll.GDO_PollChoice import GDO_PollChoice


class GDO_PollVote(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('pv_id'),
            GDT_User('pv_user').not_null(),
            GDT_Object('pv_choice').table(GDO_PollChoice.table()).not_null().cascade_delete(),
            GDT_Created('pv_created'),
        ]
