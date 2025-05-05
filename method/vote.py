from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Trans import t
from gdo.core.GDT_Object import GDT_Object
from gdo.form.GDT_Form import GDT_Form
from gdo.form.MethodForm import MethodForm
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDO_PollChoice import GDO_PollChoice
from gdo.poll.GDO_PollVote import GDO_PollVote
from gdo.poll.GDT_PollChoice import GDT_PollChoice


class vote(MethodForm):

    @classmethod
    def gdo_trigger(cls) -> str:
        return ''
    def gdo_user_type(self) -> str | None:
        return 'guest,member'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('poll').not_null().table(GDO_Poll.table()),
        ]

    def get_poll(self) -> GDO_Poll:
        return self.param_value('poll')

    def gdo_render_title(self) -> str:
        return t('mt_poll_vote')

    def gdo_render_descr(self) -> str:
        return t('md_poll_vote')

    def gdo_create_form(self, form: GDT_Form) -> None:
        poll = self.get_poll()
        form.title('%s', (poll.gdo_value('poll_title'),))
        form.text('%s', (poll.gdo_value('poll_descr'),))
        form.href(self.href(f"&poll={poll.get_id()}"))
        for i, choice in enumerate(poll.get_choices(), 1):
            form.add_field(GDT_PollChoice(f"pc{i}").label('choice', (i, choice.gdo_value('pc_text'))))
        super().gdo_create_form(form)

    def form_submitted(self):
        poll = self.get_poll()
        chosen = []
        for i, choice in enumerate(poll.get_choices(), 1):
            if self.param_value(f"pc{i}"):
                chosen.append(choice)
        return self.chosen_submitted(chosen)

    def chosen_submitted(self, chosen: list[GDO_PollChoice]):
        uid = self._env_user.get_id()
        poll = self.get_poll()

        if len(chosen) > poll.get_max_choices():
            return self.err('err_vote_max_chosen', (poll.get_max_choices(),))
        if len(chosen) < poll.get_min_choices():
            return self.err('err_vote_min_chosen', (poll.get_min_choices(),))

        # delete old
        result = (GDO_PollVote.table().select().
         join_object('pv_choice').
         where(f"pv_user={uid} AND pc_poll={poll.get_id()}").exec())
        for old in result:
            old.delete()

        for chose in chosen:
            GDO_PollVote.blank({
                'pv_user': uid,
                'pv_choice': chose.get_id(),
            }).insert()
        self.clear_form()

        Application.EVENTS.publish('poll.voted', poll, self._env_user, chosen)

        return self.msg('msg_poll_voted')
