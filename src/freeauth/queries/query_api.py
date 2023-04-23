# AUTOGENERATED FROM:
#     'src/freeauth/queries/admin/create_user.edgeql'
#     'src/freeauth/queries/admin/delete_user.edgeql'
#     'src/freeauth/queries/admin/get_user_by_exclusive_field.edgeql'
#     'src/freeauth/queries/auth/send_verify_code.edgeql'
#     'src/freeauth/queries/admin/update_user.edgeql'
#     'src/freeauth/queries/admin/update_user_status.edgeql'
#     'src/freeauth/queries/auth/validate_verify_code.edgeql'
# WITH:
#     $ edgedb-py --file src/freeauth/queries/query_api.py


from __future__ import annotations

import dataclasses
import datetime
import enum
import typing
import uuid

import edgedb


class NoPydanticValidation:
    @classmethod
    def __get_validators__(cls):
        from pydantic.dataclasses import dataclass as pydantic_dataclass

        pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


class AuthCodeType(enum.Enum):
    SMS = "SMS"
    EMAIL = "Email"


class AuthVerifyType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNUP = "SignUp"


@dataclasses.dataclass
class CreateUserResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    username: str | None
    email: str | None
    mobile: str | None
    is_deleted: bool
    created_at: datetime.datetime
    last_login_at: datetime.datetime | None


@dataclasses.dataclass
class DeleteUserResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None


@dataclasses.dataclass
class SendVerifyCodeResult(NoPydanticValidation):
    id: uuid.UUID
    created_at: datetime.datetime
    account: str
    code_type: AuthCodeType
    verify_type: AuthVerifyType
    expired_at: datetime.datetime
    ttl: int


@dataclasses.dataclass
class UpdateUserStatusResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    is_deleted: bool


class ValidateVerifyCodeResult(typing.NamedTuple):
    code_found: bool
    code_valid: bool


async def create_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str | None,
    email: str | None,
    mobile: str | None,
    hashed_password: str | None,
) -> CreateUserResult:
    return await executor.query_single(
        """\
        with
            name := <optional str>$name,
            username := <optional str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <optional str>$hashed_password
        select (
            insert User {
                name := name,
                username := username,
                email := email,
                mobile := mobile,
                hashed_password := hashed_password
            }
        ) {
            id, name, username, email, mobile,
            is_deleted, created_at, last_login_at
        };\
        """,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        hashed_password=hashed_password,
    )


async def delete_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_ids: list[uuid.UUID],
) -> list[DeleteUserResult]:
    return await executor.query(
        """\
        select (
            delete User filter .id in array_unpack(<array<uuid>>$user_ids)
        ) {id, name} order by .created_at desc;\
        """,
        user_ids=user_ids,
    )


async def get_user_by_exclusive_field(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    username: str | None,
    mobile: str | None,
    email: str | None,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            username := <optional str>$username,
            mobile := <optional str>$mobile,
            email := <optional str>$email
        SELECT
            User {
                id, name, username, email, mobile,
                is_deleted, created_at, last_login_at
            }
        FILTER (
            (
                true IF NOT EXISTS id ELSE .id = id
            )
            AND
            (
                true IF NOT EXISTS username ELSE .username = username
            )
            AND
            (
                true IF NOT EXISTS mobile ELSE .mobile = mobile
            )
            AND
            (
                true IF NOT EXISTS email ELSE .email = email
            )
            AND (EXISTS id OR EXISTS username OR EXISTS mobile OR EXISTS email)
        ) LIMIT 1\
        """,
        id=id,
        username=username,
        mobile=mobile,
        email=email,
    )


async def send_verify_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: AuthCodeType,
    verify_type: AuthVerifyType,
    code: str,
    ttl: int,
) -> SendVerifyCodeResult:
    return await executor.query_single(
        """\
        WITH
            account := <str>$account,
            code_type := <auth::CodeType>$code_type,
            verify_type := <auth::VerifyType>$verify_type,
            code := <str>$code,
            ttl := <int16>$ttl
        SELECT (
            INSERT auth::VerifyRecord {
                account := account,
                code_type := code_type,
                verify_type := verify_type,
                code := code,
                expired_at := (
                    datetime_of_transaction() +
                    <cal::relative_duration>(<str>ttl ++ ' seconds')
                )
            }
        ) {
            created_at,
            account,
            code_type,
            verify_type,
            expired_at,
            ttl := ttl
        };\
        """,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
        ttl=ttl,
    )


async def update_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str | None,
    email: str | None,
    mobile: str | None,
    id: uuid.UUID,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        with
            name := <optional str>$name,
            username := <optional str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile
        select (
            update User filter .id = <uuid>$id
            set {
                name := name,
                username := username,
                email := email,
                mobile := mobile,
            }
        ) {
            id, name, username, email, mobile,
            is_deleted, created_at, last_login_at
        };\
        """,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        id=id,
    )


async def update_user_status(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_ids: list[uuid.UUID],
    is_deleted: bool,
) -> list[UpdateUserStatusResult]:
    return await executor.query(
        """\
        with
            user_ids := <array<uuid>>$user_ids,
            is_deleted := <bool>$is_deleted
        select (
            update User filter .id in array_unpack(user_ids)
            set {
                deleted_at := datetime_of_transaction() if is_deleted else {}
            }
        ) {
            id, name, is_deleted
        } order by .created_at desc;\
        """,
        user_ids=user_ids,
        is_deleted=is_deleted,
    )


async def validate_verify_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: AuthCodeType,
    verify_type: AuthVerifyType,
    code: str,
) -> ValidateVerifyCodeResult:
    return await executor.query_single(
        """\
        WITH
            account := <str>$account,
            code_type := <auth::CodeType>$code_type,
            verify_type := <auth::VerifyType>$verify_type,
            code := <str>$code,
            record := (
                SELECT auth::VerifyRecord
                FILTER .account = account
                    AND .code_type  = code_type
                    AND .verify_type = verify_type
                    AND .code = code
                    AND .consumable
                ORDER BY .created_at DESC
                LIMIT 1
            ),
            valid_record := (
                UPDATE record
                FILTER .expired_at >= datetime_of_transaction()
                SET {
                    consumed_at := datetime_of_transaction()
                }
            ),
            valid := EXISTS record AND EXISTS valid_record,
        SELECT (
            code_found := EXISTS record,
            code_valid := EXISTS valid_record
        );\
        """,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
    )
