from typing import Self, TYPE_CHECKING
from html import escape

if TYPE_CHECKING:
    from gdo.base.GDO import GDO

from gdo.base.Trans import t
from gdo.core.GDT_Bool import GDT_Bool
from gdo.poll.GDO_Poll import GDO_Poll


class GDT_PollOutcome(GDT_Bool):
    _poll: GDO_Poll

    def gdo(self, gdo: 'GDO') -> Self:
        self._poll = self._gdo = gdo
        return self

    def poll(self, poll: GDO_Poll):
        return self.gdo(poll)

    def render_html(self) -> str:
        if not self._poll.get_id():
            return ''
        if not self._poll.is_closed():
            return escape(t('poll_results_hidden'))
        items = ''.join(
            f'<li>{escape(choice.render_title())}: {escape(choice.render_percent())}</li>'
            for choice in self._poll.get_choices()
        )
        return f'<ol class="poll-outcome">{items}</ol>'

    def render_cell(self) -> str:
        return self.render_html()

    def render_card(self) -> str:
        return self.render_html()

    def render_irc(self) -> str:
        return self.render_txt()

    def render_json(self):
        return self.render_txt()

    def render_txt(self) -> str:
        out = []
        if self._poll.get_id():
            if not self._poll.is_closed():
                return t('poll_results_hidden')
            i = 1
            for choice in self._poll.get_choices():
                out.append(t('poll_outcome', (i, choice.render_title(), choice.render_percent())))
                i += 1
        return ', '.join(out)
