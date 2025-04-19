from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.ui.GDT_Card import GDT_Card
from gdo.poll.GDO_Poll import GDO_Poll


class show_poll(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'poll'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Object('poll').not_null().table(GDO_Poll.table()),
        ]

    def get_poll(self) -> GDO_Poll:
        return self.param_value('poll')

    def gdo_execute(self) -> GDT:
        poll = self.get_poll()
        card = GDT_Card().gdo(poll)
        card.creator_header()
        card.get_content().add_field(
            poll.column('poll_title'),
            poll.column('poll_descr'),
        )
        return card
