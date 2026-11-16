import aiosmtplib
from email.message import EmailMessage
from typing import Optional

from app.services.encryption import decrypt
from app.models.email_account import EmailAccount


class SMTPService:
    def __init__(self, email_account: EmailAccount):
        self.account = email_account
        self.app_password = decrypt(email_account.app_password_encrypted)

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP."""
        msg = EmailMessage()
        msg["From"] = self.account.email_address
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.account.smtp_host,
                port=self.account.smtp_port,
                username=self.account.email_address,
                password=self.app_password,
                start_tls=True,
                timeout=30,
            )
            return True
        except Exception as e:
            print(f"[SMTP] Error sending email: {e}")
            return False

    async def send_reply(
        self,
        to: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send a reply email with proper threading headers."""
        msg = EmailMessage()
        msg["From"] = self.account.email_address
        msg["To"] = to
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.account.smtp_host,
                port=self.account.smtp_port,
                username=self.account.email_address,
                password=self.app_password,
                start_tls=True,
                timeout=30,
            )
            return True
        except Exception as e:
            print(f"[SMTP] Error sending reply: {e}")
            return False