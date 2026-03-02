from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or "",
    MAIL_FROM=settings.MAIL_DEFAULT_SENDER or settings.MAIL_USERNAME or "noreply@example.com",
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER or "smtp.example.com",
    MAIL_STARTTLS=settings.MAIL_USE_TLS,
    MAIL_SSL_TLS=settings.MAIL_USE_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: str, link: str):
    message = MessageSchema(
        subject="Verify your Memora.dev account",
        recipients=[email],
        body=f"Click the link to verify your account:\n{link}",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)
