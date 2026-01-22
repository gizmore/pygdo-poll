from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.poll.GDO_Poll import GDO_Poll


class show(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'poll'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('poll').not_null().table(GDO_Poll.table()),
        ]

    def get_poll(self) -> GDO_Poll:
        return self.param_value('poll')

    def gdo_execute(self) -> GDT:
        poll = self.get_poll()
        return poll.get_card()
