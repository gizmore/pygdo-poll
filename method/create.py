from gdo.base.IPC import IPC
from gdo.base.Application import Application
from gdo.base.Util import module_enabled
from gdo.base.util.href import href
from gdo.core.GDT_Repeat import GDT_Repeat
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.form.GDT_Form import GDT_Form
from gdo.form.GDT_Submit import GDT_Submit
from gdo.form.MethodForm import MethodForm
from gdo.message.GDT_Message import GDT_Message
from gdo.net.GDT_Redirect import GDT_Redirect
from gdo.poll.module_poll import module_poll
from gdo.ui.GDT_Title import GDT_Title
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.GDO_PollChoice import GDO_PollChoice
from gdo.date.Time import Time


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

    def gdo_transactional(self) -> bool:
        return True

    def gdo_create_form(self, form: GDT_Form) -> None:
        form.text('poll_price_per_day', (module_poll.instance().get_config_value('poll_credits_per_day'),))
        form.add_fields(
            GDT_Title('title').not_null(),
            GDT_Message('question'),
            GDT_UInt('duration_days').initial('1').not_null().min(1).max(365),
            GDT_UInt('min_answers').initial('1').not_null().min(1).max(10),
            GDT_UInt('max_answers').initial('1').not_null().min(1).max(10),
            GDT_Repeat(GDT_String('choices')).min(2).max(10).not_null(),
            GDT_Submit('add_choice').calling(self.add_choice).text('add_choice'),
        )
        super().gdo_create_form(form)

    def add_choice(self):
        pass # all good :)

    async def form_submitted(self):
        choices = self.param_value('choices')
        minimum = self.param_value('min_answers')
        maximum = self.param_value('max_answers')
        if minimum > maximum or maximum > len(choices):
            return self.err('err_poll_answer_bounds')
        days = self.param_value('duration_days')
        # Serialize schedule allocation and debit until the method transaction commits.
        Application.db().select("SELECT module_id FROM gdo_module WHERE module_name = 'poll' FOR UPDATE").fetch_row()
        unscheduled = (GDO_Poll.table().select().where('poll_closed IS NULL AND poll_expires IS NULL')
                       .first().nocache().exec().fetch_object())
        if unscheduled:
            return self.err('err_poll_legacy_unscheduled')
        last = (GDO_Poll.table().select().where('poll_closed IS NULL AND poll_expires IS NOT NULL')
                .order('poll_expires DESC').first().nocache().exec().fetch_object())
        starts = max(Application.TIME, GDO_Poll.utc_timestamp(last.gdo_val('poll_expires'))) if last else Application.TIME
        price = days * module_poll.instance().get_config_value('poll_credits_per_day')
        if price:
            if not module_enabled('payment_credits'):
                return self.err('err_method_credits_unavailable')
            from gdo.core.GDO_UserSetting import GDO_UserSetting
            uid = GDO_UserSetting.quote(self._env_user.get_id())
            result = Application.db().query(
                f"UPDATE gdo_usersetting SET uset_val = CAST(uset_val AS DECIMAL(30,0)) - {price} "
                f"WHERE uset_user = {uid} AND uset_key = 'credits' "
                f"AND CAST(uset_val AS DECIMAL(30,0)) >= {price}"
            )
            if result.rowcount != 1:
                return self.err('err_poll_insufficient_credits', (price,))
            self._env_user._vals.pop('credits', None)
            self._credits_charged = True
        poll = GDO_Poll.blank({
            'poll_title': self.param_val('title'),
            'poll_descr': self.param_val('question'),
            'poll_min_answers': self.param_val('min_answers'),
            'poll_max_answers': self.param_val('max_answers'),
            'poll_end_pending': '1',
            'poll_starts': Time.get_date(starts),
            'poll_expires': Time.get_date(starts + days * Time.ONE_DAY),
        }).insert()
        for choice in choices:
            GDO_PollChoice.blank({
                'pc_poll': poll.get_id(),
                'pc_text': choice,
            }).insert()
        self.clear_form()
        self.msg('msg_poll_created' if starts <= Application.TIME else 'msg_poll_queued', (Time.get_date(starts),) if starts > Application.TIME else None)
        # await Application.EVENTS.publish('poll.created', poll)
        self.poll = poll
        self._announce_now = starts <= Application.TIME
        module_poll.instance().get_sidebar_polls.cache_clear()
        target = 'vote' if self._announce_now else 'show'
        return GDT_Redirect().href(href('poll', target, f'&poll={poll.get_id()}')).text('You get redirected...')

    def gdo_after_execute(self):
        if hasattr(self, 'poll'):
            if getattr(self, '_credits_charged', False):
                IPC.send('base.ipc_uset', (self._env_user.get_id(), 'credits', self._env_user.get_setting_val('credits')))
