from gdo.base.GDT import GDT
from gdo.base.Util import href
from gdo.core.GDT_Object import GDT_Object
from gdo.form.GDT_Form import GDT_Form
from gdo.form.MethodForm import MethodForm
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDO_PollVote import GDO_PollVote
from gdo.poll.GDT_PollChoice import GDT_PollChoice


class vote_poll(MethodForm):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'poll.vote'

    @classmethod
    def gdo_trig(cls) -> str:
        return 'pollv'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Object('poll').not_null().table(GDO_Poll.table()),
        ]

    def get_poll_id(self):
        return self._raw_args.get_val('poll')[0]

    def get_poll(self) -> GDO_Poll:
        return GDO_Poll.table().get_by_aid(self.get_poll_id())

    def gdo_create_form(self, form: GDT_Form) -> None:
        poll = self.get_poll()
        form.text('%s', (poll.gdo_value('poll_descr'),))
        form.title('%s', (poll.gdo_value('poll_title'),))
        form.href(href('vote', 'vote_poll', f"&poll={poll.get_id()}"))
        i = 1
        for choice in poll.get_choices():
            form.add_field(GDT_PollChoice(f"pc{choice.get_id()}").label('choice', (i, choice.gdo_value('pc_text'))))
            i += 1
        super().gdo_create_form(form)

    def form_submitted(self):
        self.clear_form()
        poll = self.get_poll()
        chosen = []
        for choice in poll.get_choices():
            if self.param_value(f"pc{choice.get_id()}"):
                chosen.append(choice)
        if len(chosen) > poll.get_max_choices():
            return self.err('err_vote_max_chosen', (poll.get_max_choices(),))
        for chose in chosen:
            GDO_PollVote.blank({
                'pv_user': self._env_user.get_id(),
                'pv_choice': chose.get_id(),
            }).insert()
        return self.msg('msg_vote_voted_poll')
