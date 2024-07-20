import smtplib
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from app.db.queries.user_queries import UserQueries
from app.db.queries.recovery_token_queries import RecoveryTokenQueries


class EmailService:
    login = os.environ.get('EMAIL_LOGIN')
    password = os.environ.get('EMAIL_PASSWORD')
    expiration_days_recovery_token = 3

    def __init__(self):
        self.welcome_template = self.load_template('../templates/welcome_email.html')
        self.forgot_password_template = self.load_template('../templates/forgot_password_email.html')

    def load_template(self, filepath):
        working_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(working_dir, filepath), 'r') as file:
            return file.read()

    def send_email(self, destination, subject, body, mime_type='plain'):
        msg = MIMEMultipart()
        msg['From'] = self.login
        msg['To'] = destination
        msg['Subject'] = subject
        msg.attach(MIMEText(body, mime_type))

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(self.login, self.password)
            smtp.sendmail(self.login, destination, msg.as_string())
        return True

    def send_forgot_password_email(self, user):
        code = str(random.randint(100000, 999999))
        now = datetime.now()
        expiration_date = now + timedelta(days=self.expiration_days_recovery_token)
        RecoveryTokenQueries.create(code, now, expiration_date, user['id'])
        body = self.forgot_password_template.replace("{{ code }}", code)
        return self.send_email(user['email'], "Recuperação de senha", body, 'html')

    def send_welcome_email(self, destination, name):
        body = self.welcome_template.replace("{{ name }}", name)
        return self.send_email(destination, "Bem vindo ao Votaai!", body, 'html')
