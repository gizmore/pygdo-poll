from gdo.base.Util import href
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Repeat import GDT_Repeat
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.form.GDT_Form import GDT_Form
from gdo.form.GDT_Submit import GDT_Submit
from gdo.form.MethodForm import MethodForm
from gdo.message.GDT_Message import GDT_Message
from gdo.net.GDT_Redirect import GDT_Redirect
from gdo.ui.GDT_Title import GDT_Title
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDO_PollChoice import GDO_PollChoice


class create(MethodForm):

    @classmethod
    def gdo_trigger(cls) -> str:
        return "poll.add"

    @classmethod
    def gdo_trig(cls) -> str:
        return 'polla'

    def gdo_create_form(self, form: GDT_Form) -> None:
        form.add_field(
            GDT_Title('title').not_null(),
            GDT_Message('question'),
            GDT_UInt('max_answers').initial('1').not_null().min(1).max(10),
            GDT_Repeat(GDT_String('choices')).min(2).max(10).not_null(),
            GDT_Submit('add_choice').calling(self.add_choice).text('add_choice'),
        )
        super().gdo_create_form(form)

    def add_choice(self):
        pass # all good :)

    def form_submitted(self):
        poll = GDO_Poll.blank({
            'poll_title': self.param_val('title'),
            'poll_descr': self.param_val('question'),
            'poll_max_answers': self.param_val('max_answers'),
        }).insert()
        choices = self.param_value('choices')
        for choice in choices:
            GDO_PollChoice.blank({
                'pc_poll': poll.get_id(),
                'pc_text': choice,
            }).insert()
        self.clear_form()
        self.msg('msg_poll_created')
        return GDT_Redirect().href(href('vote', 'vote_poll', f'&poll={poll.get_id()}')).text('test')
