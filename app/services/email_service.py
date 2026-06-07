from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import Optional


class EmailService:
    def __init__(
        self,
        mail_username: str,
        mail_password: str,
        mail_from: str,
        mail_server: str,
        mail_port: int,
        use_ssl: bool = False,
        use_tls: bool = True
    ):
        self.mail_from = mail_from
        self.conf = ConnectionConfig(
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_FROM=mail_from,
            MAIL_SERVER=mail_server,
            MAIL_PORT=mail_port,
            MAIL_SSL_TLS=use_ssl,
            MAIL_STARTTLS=use_tls,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

    async def send_email(
        self,
        recipient: str,
        subject: str,
        html_body: str
    ) -> None:
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=html_body,
            subtype=MessageType.html
        )
        
        fm = FastMail(self.conf)
        await fm.send_message(message)

    async def send_verification_otp(
        self,
        email: str,
        otp_code: str
    ) -> None:
        subject = "Verify Your BitBound Account"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Email Verification</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #4F46E5;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    background-color: #f4f4f4;
                    border-radius: 5px;
                    letter-spacing: 5px;
                    font-family: monospace;
                }}
                .warning {{
                    color: #e53e3e;
                    font-size: 14px;
                    text-align: center;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #e0e0e0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Verify Your BitBound Account</h2>
                </div>
                <p>Hello,</p>
                <p>Thank you for registering with BitBound Pay. Please use the following One-Time Password (OTP) to verify your email address:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This OTP will expire in <strong>10 minutes</strong>.</p>
                <p>If you did not create an account with BitBound Pay, please ignore this email.</p>
                <div class="warning">
                    ⚠️ Never share this OTP with anyone. BitBound Pay will never ask for your OTP.
                </div>
                <div class="footer">
                    <p>&copy; 2024 BitBound Pay. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        await self.send_email(email, subject, html_body)

    async def send_password_reset_otp(
        self,
        email: str,
        otp_code: str
    ) -> None:
        subject = "Reset Your BitBound Password"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Password Reset</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #4F46E5;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    background-color: #f4f4f4;
                    border-radius: 5px;
                    letter-spacing: 5px;
                    font-family: monospace;
                }}
                .warning {{
                    color: #e53e3e;
                    font-size: 14px;
                    text-align: center;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #e0e0e0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Reset Your BitBound Password</h2>
                </div>
                <p>Hello,</p>
                <p>We received a request to reset your password for your BitBound Pay account. Use the following One-Time Password (OTP) to proceed:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This OTP will expire in <strong>10 minutes</strong>.</p>
                <p>If you did not request a password reset, please ignore this email or contact support.</p>
                <div class="warning">
                    ⚠️ Never share this OTP with anyone. BitBound Pay will never ask for your OTP.
                </div>
                <div class="footer">
                    <p>&copy; 2024 BitBound Pay. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        await self.send_email(email, subject, html_body)
