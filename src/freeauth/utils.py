from __future__ import annotations

import random
import secrets
import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MOBILE_REGEX = r"^1[3-9]\d{9}$"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def gen_random_string(
    size: int, letters: str | None = None, secret: bool = False
) -> str:
    letters: str = letters or string.ascii_lowercase + string.digits
    if secret:
        return "".join(secrets.choice(letters) for _ in range(size))
    else:
        return "".join(random.choices(letters, k=size))
