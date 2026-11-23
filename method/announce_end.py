from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.base.Trans import Trans
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Object import GDT_Object
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.poll.method.announce import announce


class announce_end(Method):
    def gdo_method_hidden(self):
        return True

    def gdo_user_permission(self):
        return GDO_Permission.CRONJOB

    def gdo_parameters(self):
        return [GDT_Object('id').table(GDO_Poll.table()).not_null()]

    async def gdo_execute(self):
        if not (Application.IS_DOG or Application.is_unit_test()):
            return self.empty()
        poll = self.param_value('id')
        if not poll.is_closed():
            return self.empty()
        title = poll.render_title()
        results = ', '.join(f"{choice.render_title()}: {int(choice._vals.get('num_votes') or 0)}"
                            for choice in poll.get_choices())
        subscriber_method = announce()
        for channel in GDO_Channel.with_setting(subscriber_method, 'subscribed', '1', '1'):
            try:
                with Trans(channel.get_lang_iso()):
                    await channel.send_text('msg_poll_end_announce', (title, results))
            except Exception as error:
                Logger.error(f'Poll end channel delivery failed ({type(error).__name__}).')
        for user in GDO_User.table().with_settings_result([('msg_polls', '=', '1')]):
            try:
                with Trans(user.get_setting_val('language')):
                    await user.send('msg_poll_end_announce', (title, results))
            except Exception as error:
                Logger.error(f'Poll end user delivery failed ({type(error).__name__}).')
        from gdo.poll.method.mail import mail
        mail().mail_results(poll, results)
        return self.empty()
