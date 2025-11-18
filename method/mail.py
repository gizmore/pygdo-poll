from gdo.base.GDT import GDT
from gdo.base.Render import Mode
from gdo.base.Result import Result
from gdo.base.Trans import Trans, sitename, t
from gdo.base.util.href import url
from gdo.core.GDO_Method import GDO_Method
from gdo.core.GDO_User import GDO_User
from gdo.core.MethodCronjob import MethodCronjob
from gdo.date.Time import Time
from gdo.mail.Mail import Mail
from gdo.poll.GDO_PollChoice import GDO_PollChoice
from gdo.poll.method.vote import vote
from gdo.poll.module_poll import module_poll
from gdo.poll.GDO_Poll import GDO_Poll
from gdo.ui.GDT_Link import GDT_Link


class mail(MethodCronjob):
    """
    New Poll created mailer cronjob.
    @ToDO: Chappy: review
    """

    def mod(self) -> module_poll:
        return module_poll.instance()

    def gdo_execute(self) -> GDT:
        if self.mod().cfg_email_new_polls():
            if poll := GDO_Poll.table().select().where('poll_announced IS NULL').order('poll_id ASC').first().exec().fetch_object():
                # poll.save_val('poll_announced', Time.get_date())
                self.mail_poll(poll)
        return self.empty()

    def get_users(self) -> Result:
        if self.mod().cfg_email_all_users():
            settings = [('email_confirmed', '=', '1')]
        else:
            settings = [('email_new_polls', '=', '1'), ('email_confirmed', 'IS NOT', None)]
        return GDO_User.table().with_settings_result(settings).nocache()

    def mail_poll(self, poll: GDO_Poll):
        choices = poll.get_choices()
        for user in self.get_users():
            self.mail_poll_to_user(poll, choices, user)

    def mail_poll_to_user(self, poll: GDO_Poll, choices: list[GDO_PollChoice], user: GDO_User):
        with Trans(user.get_lang_iso()):
            self.send_mail_to_user(poll, choices, user)

    def send_mail_to_user(self, poll: GDO_Poll, choices: list[GDO_PollChoice], user: GDO_User):
        mail = Mail.from_bot()
        links = []
        token = vote().create_autologin_token(user.get_id())
        if poll.is_multiple_choice():
            link = GDT_Link().href(url('poll', 'vote', f"&poll={poll.get_id()}&_auth={token}"))
            links.append(link.render_mail())
        else:
            for i, choice in enumerate(choices, 1):
                link = GDT_Link().href(url('poll', 'vote', f"&poll={poll.get_id()}&pc{i}=1&_auth={token}"))
                links.append(link.render_mail())
        args = (
            user.render_name(),
            sitename(),
            poll.render_title(),
            poll.render_descr(Mode.render_mail),
            "<br/>\n".join(links),
        )
        mail.subject(t('mails_poll_created', (poll.render_title(),)))
        mail.body(t('mailb_poll_created', args))
        mail.send_to_user(user)
