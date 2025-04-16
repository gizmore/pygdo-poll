from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Created import GDT_Created
from gdo.message.GDT_Message import GDT_Message
from gdo.ui.GDT_Title import GDT_Title
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gdo.poll.GDO_PollChoice import GDO_PollChoice


class GDO_Poll(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('poll_id'),
            GDT_Title('poll_title').maxlen(192).not_null(),
            GDT_Message('poll_descr'),
            GDT_UInt('poll_max_answers').bytes(1).not_null().initial('1'),
            # GDT_Join('poll_top_answer'),
            GDT_Creator('poll_creator'),
            GDT_Created('poll_created'),
        ]

    def get_choices(self) -> list['GDO_PollChoice']:
        from gdo.poll.GDO_PollChoice import GDO_PollChoice
        return GDO_PollChoice.table().select().where(f"pc_poll={self.get_id()}").exec().fetch_all()

    def get_max_choices(self) -> int:
        return self.gdo_value('poll_max_answers')
