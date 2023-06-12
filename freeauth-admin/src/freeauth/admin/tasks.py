from __future__ import annotations

from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from . import logger


class MailSettings(ConnectionConfig):
    MAIL_FROM_NAME = "FreeAuth"
    TEMPLATE_FOLDER: Path = (
        Path(__file__).resolve().parent.parent / "templates/email"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


mail_conf = MailSettings()


async def send_email(tpl: str, subject: str, to: EmailStr, body: dict):
    logger.info(
        "Sending email %s to account %s with data: %r", subject, to, body
    )
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        template_body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(mail_conf)
    await fm.send_message(message, template_name=tpl)