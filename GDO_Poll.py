from functools import lru_cache

from gdo.base.GDT import GDT
from gdo.base.GDO import GDO
from gdo.base.Render import Mode
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Text import GDT_Text
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.ui.GDT_Card import GDT_Card
from gdo.ui.GDT_Title import GDT_Title
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gdo.poll.GDO_PollChoice import GDO_PollChoice


class GDO_Poll(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('poll_id'),
            GDT_Title('poll_title').label('title').maxlen(192).not_null(),
            GDT_Text('poll_descr').label('description'),
            GDT_UInt('poll_min_answers').bytes(1).not_null().initial('1'),
            GDT_UInt('poll_max_answers').bytes(1).not_null().initial('1'),
            GDT_Timestamp('poll_announced'),
            GDT_Timestamp('poll_closed'),
            GDT_Creator('poll_creator'),
            GDT_Created('poll_created'),
        ]

    def get_descr_column(self) -> GDT_Text:
        return GDT_Text.column(self, 'poll_descr')

    def render_title(self) -> str:
        return self.gdo_val('poll_title')

    def render_descr(self, mode: Mode=Mode.render_html) -> str:
        return self.get_descr_column().render(mode)

    def get_choices(self) -> list['GDO_PollChoice']:
        from gdo.poll.GDO_PollChoice import GDO_PollChoice
        return (GDO_PollChoice.table().select().
                select("(SELECT COUNT(*) FROM gdo_pollvote WHERE pv_choice=pc_id) num_votes").
                select(f"(SELECT COUNT(*) FROM gdo_pollvote JOIN gdo_pollchoice ON pc_id=pv_choice WHERE pc_poll={self.get_id()}) total_votes").
                where(f"pc_poll={self.get_id()}").
                nocache().exec().fetch_all())

    def get_min_choices(self) -> int:
        return self.gdo_value('poll_min_answers')

    def get_max_choices(self) -> int:
        return self.gdo_value('poll_max_answers')

    def is_multiple_choice(self) -> bool:
        return self.get_max_choices() > 1

    def get_card(self):
        from gdo.poll.GDT_PollOutcome import GDT_PollOutcome
        card = GDT_Card().gdo(self)
        card.creator_header()
        card.get_content().add_fields(
            self.column('poll_title'),
            self.column('poll_descr'),
            GDT_PollOutcome('poll_outcome').gdo(self),
        )
        return card
