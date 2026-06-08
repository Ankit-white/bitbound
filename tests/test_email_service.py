import pytest

from app.services.email_service import EmailService


class FakeSMTP:
    sent_messages = []
    login_calls = []

    def __init__(self, server: str, port: int, timeout: int):
        self.server = server
        self.port = port
        self.timeout = timeout
        self.started_tls = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username: str, password: str):
        self.login_calls.append((username, password))

    def send_message(self, message, from_addr=None, to_addrs=None):
        self.sent_messages.append(
            {
                "from_addr": from_addr,
                "to_addrs": to_addrs,
                "header_to": message["To"],
                "header_from": message["From"],
            }
        )


@pytest.mark.anyio("asyncio")
async def test_verification_email_uses_registered_email_as_recipient(monkeypatch):
    FakeSMTP.sent_messages = []
    FakeSMTP.login_calls = []
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSMTP)

    service = EmailService(
        mail_username="sender@example.com",
        mail_password="app-password",
        mail_from="sender@example.com",
        mail_server="smtp.example.com",
        mail_port=587,
        use_ssl=False,
        use_tls=True,
    )

    await service.send_verification_otp(
        email="registered-user@example.com",
        otp_code="Aa1@Bb2#",
    )

    assert FakeSMTP.login_calls == [("sender@example.com", "app-password")]
    assert FakeSMTP.sent_messages == [
        {
            "from_addr": "sender@example.com",
            "to_addrs": ["registered-user@example.com"],
            "header_to": "registered-user@example.com",
            "header_from": "sender@example.com",
        }
    ]
