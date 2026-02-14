from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Trans import tiso, Trans
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Object import GDT_Object
from gdo.poll.GDO_Poll import GDO_Poll


class announce(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return ''

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('id').table(GDO_Poll.table()).not_null(),
        ]

    def gdo_method_config_channel(cls) -> list[GDT]:
        return [
            GDT_Bool('subscribed').initial('1').not_null(),
        ]

    def get_poll(self) -> GDO_Poll:
        return self.param_value('id')

    async def gdo_execute(self) -> GDT:
        if Application.IS_DOG or Application.is_unit_test():
            poll = self.get_poll()
            choice_out = []
            i = 1
            for choice in poll.get_choices():
                choice_out.append(f"{i}) {choice.gdo_val('pc_text')}")
                i += 1
            args = (poll.column('poll_descr').render_txt(), poll.column('poll_title').render_txt(), poll.get_id(), ", ".join(choice_out), poll.get_id())
            for channel in GDO_Channel.with_setting(self, 'subscribed', '1', '1'):
                with Trans(channel.get_lang_iso()):
                    await channel.send_text('msg_poll_announce', args)
            for user in GDO_User.table().with_settings_result([('msg_polls', '=', '1')]):
                with Trans(user.get_setting_val('language')):
                    await user.send('msg_poll_announce', args)
        return self.empty()
