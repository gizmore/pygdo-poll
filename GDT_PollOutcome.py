from gdo.base.Trans import t
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Template import GDT_Template
from gdo.poll.GDO_Poll import GDO_Poll


class GDT_PollOutcome(GDT_Bool):
    _poll: GDO_Poll

    def poll(self, poll: GDO_Poll):
        self._poll = poll
        return self

    def render_cell(self) -> str:
        return GDT_Template.python('poll', 'cell_poll_outcome.html', {'field': self})

    def render_txt(self) -> str:
        out = []
        for choice in self._poll.get_choices():
            out.append(t('poll_outcome', (choice.render_title(), choice.render_percent())))
        return ', '.join(out)
