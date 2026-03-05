import aiosmtplib
from email.message import EmailMessage
from config import settings


async def send_otp_email(to_email: str, otp_code: str) -> None:
    if settings.test_otp_code:
        # In test mode, skip sending
        return

    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = "Your Movie Picker verification code"
    msg.set_content(
        f"Your one-time verification code is: {otp_code}\n\n"
        f"This code expires in 10 minutes.\n\n"
        f"If you didn't request this, you can ignore this email."
    )

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )
