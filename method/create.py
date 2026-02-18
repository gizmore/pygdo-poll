from gdo.base.Cache import Cache
from gdo.base.IPC import IPC
from gdo.base.util.href import href
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
    """
    Create a Poll via http or a text connector like Telegram
    """

    @classmethod
    def gdo_trigger(cls) -> str:
        return "poll.add"

    @classmethod
    def gdo_trig(cls) -> str:
        return 'polla'

    def gdo_create_form(self, form: GDT_Form) -> None:
        form.add_fields(
            GDT_Title('title').not_null(),
            GDT_Message('question'),
            GDT_UInt('min_answers').initial('1').not_null().min(1).max(10),
            GDT_UInt('max_answers').initial('1').not_null().min(1).max(10),
            GDT_Repeat(GDT_String('choices')).min(2).max(10).not_null(),
            GDT_Submit('add_choice').calling(self.add_choice).label('add_choice'),
        )
        super().gdo_create_form(form)

    def add_choice(self):
        pass # all good :)

    async def form_submitted(self):
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
        # await Application.EVENTS.publish('poll.created', poll)
        self.poll = poll
        Cache.remove()
        return GDT_Redirect().href(href('poll', 'vote', f'&poll={poll.get_id()}')).text('You get redirected...')

    def gdo_after_execute(self):
        if hasattr(self, 'poll'):
            IPC.send('poll.announce', (self.poll.get_id(),))
