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
        self.msg['From'] = 'donotreply@ltu.edu' + ' < rmedoro@ltu.edu >'
        self.msg['To'] = recipient
        self.msg.add_header('reply-to', 'rmedoro@ltu.edu')
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
        password = self._set_password()
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
        self._smtp_server.sendmail('progressTracker@ltu.edu', self._recipient, text)

    def _disconnect(self) -> None:
        self._smtp_server.quit()


if __name__ == '__main__':
    selected_courses = ['INT_1213', 'INT_4444', 'INT_9999', "MGT_9999"]
    message = "Attention Advisors:\n\nRomeo has requested approval to take the following courses:\n"
    for c in selected_courses:
        message = message + "\t" + c + "\n"

    message = message + 'Please address this request at your earliest convenience.\n\n'
    message = message + "Sincerely,\n\nLTU Progress Tracker"

    email_handler = EmailHandler('romeo.medoro@gmail.com')
    email_handler.send_email(message)