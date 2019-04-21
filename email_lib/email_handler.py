import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailHandler:
    def __init__(self, recipient: str):
        self._smtp_server = None
        self._recipient = recipient
        self.msg = MIMEMultipart()
        self.msg['Subject'] = 'A New Course Request Awaits Your Approval'
        self.msg['To'] = recipient
        self.sender = ''
        self._connect()

    @staticmethod
    def _set_sender() -> str:
        with open('secret.json') as f:
            shh = json.load(f)

        return shh.get('email_sender')

    @staticmethod
    def _set_password() -> str:
        with open('secret.json') as f:
            shh = json.load(f)

        return shh.get('email_pass')

    def _connect(self) -> None:
        sender = self._set_sender()
        self.sender = sender
        password = self._set_password()
        self.msg['From'] = 'donotreply@ltu.edu' + ' < ' + sender + ' >'
        self._smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self._smtp_server.login(sender, password)

    def send_email(self, message: str) -> None:
        msg_list = message.split('\n')
        html = """<html><head></head><body>"""

        for string in msg_list:
            html = html + "<p>{}</p>".format(string)
        html = html + '</body></html>'
        self.msg.attach(MIMEText(html, 'html'))

        text = self.msg.as_string()
        self._smtp_server.sendmail(self.sender, self._recipient, text)

    def _disconnect(self) -> None:
        self._smtp_server.quit()

