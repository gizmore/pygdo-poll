from gdo.core.Connector import Connector
from gdo.core.GDT_Repeat import GDT_Repeat
from gdo.core.GDT_UInt import GDT_UInt
from gdo.form.GDT_Form import GDT_Form
from gdo.poll.method.vote import vote


class vote_cli(vote):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'poll.vote'

    @classmethod
    def gdo_trig(cls) -> str:
        return 'pv'

    def gdo_connectors(self) -> str:
        return Connector.text_connectors()

    def gdo_create_form(self, form: GDT_Form) -> None:
        poll = self.get_poll()
        form.title('%s', (poll.gdo_value('poll_title'),))
        form.text('%s', (poll.gdo_value('poll_descr'),))
        form.href(self.href(f"&poll={poll.get_id()}"))
        choices = poll.get_choices()
        form.add_field(GDT_Repeat(GDT_UInt('choose').min(1).max(len(choices))).min(poll.get_min_choices()).max(poll.get_max_choices()))
        super().gdo_create_form(form)

    def form_submitted(self):
        poll = self.get_poll()
        choose = self.param_value('choose')
        choices = poll.get_choices()
        chosen = []
        for c in choose:
            chosen.append(choices[c-1])
        return self.chosen_submitted(chosen)
