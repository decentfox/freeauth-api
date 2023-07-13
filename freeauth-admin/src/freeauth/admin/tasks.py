from __future__ import annotations

import json
from pathlib import Path

from alibabacloud_dysmsapi20170525 import client as ali_sms_client
from alibabacloud_dysmsapi20170525 import models as ali_sms_models
from alibabacloud_tea_openapi.models import Config as AliyunConfig
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseSettings, EmailStr
from tencentcloud.common import credential
from tencentcloud.sms.v20210111 import models as tq_sms_models
from tencentcloud.sms.v20210111 import sms_client as tq_sms_client

from freeauth.conf.settings import get_settings

from . import logger


class MailSettings(ConnectionConfig):
    MAIL_FROM_NAME: str = "FreeAuth"
    MAIL_FROM: EmailStr | None = None
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_PORT: int = 25
    MAIL_SERVER: str = "localhost"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = False
    TEMPLATE_FOLDER: Path = Path(__file__).resolve().parent / "templates/email"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


mail_conf = MailSettings()


class SMSSettings(BaseSettings):
    SMS_PROVIDER: str | None = None  # 'tencent-cloud' or 'aliyun'
    SMS_SECRET_ID: str | None = None
    SMS_SECRET_KEY: str | None = None
    SMS_SIGN_NAME: str | None = None
    SMS_REGION: str | None = None
    SMS_APP_ID: str | None = None

    # Template IDs/Codes
    SMS_AUTH_CODE_TPL_ID: str | None = None  # send auth code

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


sms_conf = SMSSettings()


def is_func_enabled(account):
    settings = get_settings()
    return not settings.testing and account not in settings.demo_accounts


class TencentSMSProvider:
    def __init__(self):
        cred = credential.Credential(
            sms_conf.SMS_SECRET_ID, sms_conf.SMS_SECRET_KEY
        )
        self.client = tq_sms_client.SmsClient(cred, sms_conf.SMS_REGION)
        logger.info("TencentCloud SMS provider loaded")

    def send_auth_code(self, phone_num: str, code: str, ttl: int):
        if not is_func_enabled(phone_num):
            return

        try:
            req = tq_sms_models.SendSmsRequest()
            req.SmsSdkAppId = sms_conf.SMS_APP_ID
            req.SignName = sms_conf.SMS_SIGN_NAME
            req.TemplateId = sms_conf.SMS_AUTH_CODE_TPL_ID
            req.TemplateParamSet = [code, str(ttl)]
            req.PhoneNumberSet = [phone_num]
            logger.info("Sending sms request with params %r", req)
            resp: tq_sms_models.SendSmsResponse = self.client.SendSms(req)
            status: tq_sms_models.SendStatus = resp.SendStatusSet[0]
            if status.Code != "Ok":
                logger.error("Failed to send sms, got error response %r", resp)
            else:
                logger.info("Got sms sending response %r", resp)
        except Exception as error:
            logger.error("Failed to send sms request %r", error)


class AliyunSMSProvider:
    def __init__(self):
        self.client = ali_sms_client.Client(
            AliyunConfig(
                access_key_id=sms_conf.SMS_SECRET_ID,
                access_key_secret=sms_conf.SMS_SECRET_KEY,
                endpoint="dysmsapi.aliyuncs.com",
            )
        )
        logger.info("Aliyun SMS provider loaded")

    def send_auth_code(self, phone_num: str, code: str, ttl: int):
        if not is_func_enabled(phone_num):
            return

        try:
            req = ali_sms_models.SendSmsRequest(
                phone_numbers=phone_num,
                sign_name=sms_conf.SMS_SIGN_NAME,
                template_code=sms_conf.SMS_AUTH_CODE_TPL_ID,
                # Aliyun only supports the `code` parameter.
                # https://help.aliyun.com/document_detail/463237.html?spm=a2c4g.108253.0.0.666d7f33lMeLAS#section-9tx-f7q-end
                template_param=json.dumps(dict(code=code)),
            )
            logger.info("Sending sms request with params %s", req)
            resp = self.client.send_sms(req)
            logger.info("Got sms sending response %s", resp)
        except Exception as error:
            logger.error("Failed to send sms request %s", error)


sms_provider: TencentSMSProvider | AliyunSMSProvider | None = None


def init_app():
    global sms_provider
    if sms_conf.SMS_PROVIDER == "tencent-cloud":
        sms_provider = TencentSMSProvider()
    elif sms_conf.SMS_PROVIDER == "aliyun":
        sms_provider = AliyunSMSProvider()


async def send_email(tpl: str, subject: str, to: str, body: dict):
    if not is_func_enabled(to):
        return

    logger.info(
        "Sending email %s to account %s with data: %r", subject, to, body
    )
    message = MessageSchema(
        subject=subject,
        recipients=[EmailStr(to)],
        template_body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(mail_conf)
    await fm.send_message(message, template_name=tpl)
