# AUTOGENERATED FROM:
#     'src/freeauth/db/auth/queries/create_audit_log.edgeql'
#     'src/freeauth/db/auth/queries/get_current_user.edgeql'
#     'src/freeauth/db/auth/queries/get_login_setting.edgeql'
#     'src/freeauth/db/auth/queries/get_login_setting_by_key.edgeql'
#     'src/freeauth/db/auth/queries/get_user_by_access_token.edgeql'
#     'src/freeauth/db/auth/queries/get_user_by_account.edgeql'
#     'src/freeauth/db/auth/queries/has_any_permission.edgeql'
#     'src/freeauth/db/auth/queries/send_code.edgeql'
#     'src/freeauth/db/auth/queries/sign_in.edgeql'
#     'src/freeauth/db/auth/queries/sign_out.edgeql'
#     'src/freeauth/db/auth/queries/sign_up.edgeql'
#     'src/freeauth/db/auth/queries/update_profile.edgeql'
#     'src/freeauth/db/auth/queries/update_pwd.edgeql'
#     'src/freeauth/db/auth/queries/upsert_login_setting.edgeql'
#     'src/freeauth/db/auth/queries/validate_account.edgeql'
#     'src/freeauth/db/auth/queries/validate_code.edgeql'
# WITH:
#     $ edgedb-py --target async --dir src/freeauth/db/auth --file src/freeauth/db/auth/auth_qry_async_edgeql.py


from __future__ import annotations
import dataclasses
import datetime
import edgedb
import enum
import typing
import uuid


class NoPydanticValidation:
    @classmethod
    def __get_validators__(cls):
        from pydantic.dataclasses import dataclass as pydantic_dataclass
        pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


@dataclasses.dataclass
class CreateAuditLogResult(NoPydanticValidation):
    id: uuid.UUID
    client_ip: str
    os: str | None
    device: str | None
    browser: str | None
    status_code: FreeauthAuditStatusCode
    is_succeed: bool
    event_type: FreeauthAuditEventType
    created_at: datetime.datetime
    user: CreateAuditLogResultUser


@dataclasses.dataclass
class CreateAuditLogResultUser(NoPydanticValidation):
    id: uuid.UUID
    username: str | None
    mobile: str | None
    email: str | None


class FreeauthAuditEventType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNOUT = "SignOut"
    SIGNUP = "SignUp"
    RESETPWD = "ResetPwd"
    CHANGEPWD = "ChangePwd"


class FreeauthAuditStatusCode(enum.Enum):
    OK = "OK"
    ACCOUNT_ALREADY_EXISTS = "ACCOUNT_ALREADY_EXISTS"
    ACCOUNT_NOT_EXISTS = "ACCOUNT_NOT_EXISTS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    PASSWORD_ATTEMPTS_EXCEEDED = "PASSWORD_ATTEMPTS_EXCEEDED"
    INVALID_CODE = "INVALID_CODE"
    CODE_INCORRECT = "CODE_INCORRECT"
    CODE_ATTEMPTS_EXCEEDED = "CODE_ATTEMPTS_EXCEEDED"
    CODE_EXPIRED = "CODE_EXPIRED"


class FreeauthCodeType(enum.Enum):
    SMS = "SMS"
    EMAIL = "Email"


class FreeauthVerifyType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNUP = "SignUp"


@dataclasses.dataclass
class GetCurrentUserResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    username: str | None
    email: str | None
    mobile: str | None
    org_type: GetCurrentUserResultOrgType | None
    departments: list[GetCurrentUserResultDepartmentsItem]
    roles: list[GetCurrentUserResultRolesItem]
    perms: list[str]
    is_deleted: bool
    created_at: datetime.datetime
    last_login_at: datetime.datetime | None
    reset_pwd_on_next_login: bool | None


@dataclasses.dataclass
class GetCurrentUserResultDepartmentsItem(NoPydanticValidation):
    id: uuid.UUID
    code: str | None
    name: str
    enterprise: GetCurrentUserResultDepartmentsItemEnterprise | None
    org_type: GetCurrentUserResultDepartmentsItemEnterprise | None


@dataclasses.dataclass
class GetCurrentUserResultDepartmentsItemEnterprise(NoPydanticValidation):
    id: uuid.UUID
    name: str


@dataclasses.dataclass
class GetCurrentUserResultOrgType(NoPydanticValidation):
    id: uuid.UUID
    code: str | None
    name: str


@dataclasses.dataclass
class GetCurrentUserResultRolesItem(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None
    description: str | None
    org_type: GetCurrentUserResultOrgType | None
    is_deleted: bool
    is_protected: bool
    created_at: datetime.datetime


@dataclasses.dataclass
class GetLoginSettingResult(NoPydanticValidation):
    id: uuid.UUID
    key: str
    value: str


@dataclasses.dataclass
class GetUserByAccessTokenResult(NoPydanticValidation):
    id: uuid.UUID
    access_token: str
    user: GetUserByAccessTokenResultUser


@dataclasses.dataclass
class GetUserByAccessTokenResultUser(NoPydanticValidation):
    id: uuid.UUID


@dataclasses.dataclass
class GetUserByAccountResult(NoPydanticValidation):
    id: uuid.UUID
    is_deleted: bool


@dataclasses.dataclass
class SendCodeResult(NoPydanticValidation):
    id: uuid.UUID
    created_at: datetime.datetime
    account: str
    code_type: FreeauthCodeType
    verify_type: FreeauthVerifyType
    expired_at: datetime.datetime
    ttl: int


@dataclasses.dataclass
class SignInResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    username: str | None
    email: str | None
    mobile: str | None
    org_type: GetCurrentUserResultOrgType | None
    departments: list[SignInResultDepartmentsItem]
    roles: list[SignInResultRolesItem]
    is_deleted: bool
    created_at: datetime.datetime
    last_login_at: datetime.datetime | None


@dataclasses.dataclass
class SignInResultDepartmentsItem(NoPydanticValidation):
    id: uuid.UUID
    code: str | None
    name: str


@dataclasses.dataclass
class SignInResultRolesItem(NoPydanticValidation):
    id: uuid.UUID
    code: str | None
    name: str


@dataclasses.dataclass
class SignOutResult(NoPydanticValidation):
    id: uuid.UUID


@dataclasses.dataclass
class UpsertLoginSettingResult(NoPydanticValidation):
    id: uuid.UUID


@dataclasses.dataclass
class ValidateAccountResult(NoPydanticValidation):
    id: uuid.UUID
    hashed_password: str | None
    is_deleted: bool
    recent_failed_attempts: int


class ValidateCodeResult(typing.NamedTuple):
    status_code: FreeauthAuditStatusCode


async def create_audit_log(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_id: uuid.UUID,
    client_info: str,
    status_code: FreeauthAuditStatusCode,
    event_type: FreeauthAuditEventType,
) -> CreateAuditLogResult:
    return await executor.query_single(
        """\
        with
            module freeauth,
            user := (
                select User filter .id = <uuid>$user_id
            ),
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            status_code := <AuditStatusCode>$status_code
        select (
            insert AuditLog {
                client_ip := <str>client_info.client_ip,
                event_type := <AuditEventType>$event_type,
                status_code := status_code,
                raw_ua := <str>client_info.user_agent['raw_ua'],
                os := <str>client_info.user_agent['os'],
                device := <str>client_info.user_agent['device'],
                browser := <str>client_info.user_agent['browser'],
                user := user
            }
        ) {
            client_ip,
            os,
            device,
            browser,
            status_code,
            is_succeed,
            event_type,
            created_at,
            user: {
                username,
                mobile,
                email
            }
        };\
        """,
        user_id=user_id,
        client_info=client_info,
        status_code=status_code,
        event_type=event_type,
    )


async def get_current_user(
    executor: edgedb.AsyncIOExecutor,
) -> GetCurrentUserResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            user := global current_user,
            perms := (
                select user.permissions
                filter .application = global current_app
            )
        select user {
            name,
            username,
            email,
            mobile,
            org_type: { code, name },
            departments := (
                select .directly_organizations {
                    id,
                    code,
                    name,
                    enterprise := assert_single(.ancestors {
                        id,
                        name
                    } filter exists [is Enterprise]),
                    org_type := assert_single(.ancestors {
                        id,
                        name
                    } filter exists [is OrganizationType])
                }
            ),
            roles: {
                name,
                code,
                description,
                org_type: { code, name },
                is_deleted,
                is_protected,
                created_at
            },
            perms := array_agg(perms.code),
            is_deleted,
            created_at,
            last_login_at,
            reset_pwd_on_next_login
        };\
        """,
    )


async def get_login_setting(
    executor: edgedb.AsyncIOExecutor,
) -> list[GetLoginSettingResult]:
    return await executor.query(
        """\
        select freeauth::LoginSetting { key, value } order by .key;\
        """,
    )


async def get_login_setting_by_key(
    executor: edgedb.AsyncIOExecutor,
    *,
    key: str,
) -> GetLoginSettingResult | None:
    return await executor.query_single(
        """\
        select freeauth::LoginSetting { key, value } filter .key = <str>$key;\
        """,
        key=key,
    )


async def get_user_by_access_token(
    executor: edgedb.AsyncIOExecutor,
    *,
    access_token: str,
) -> GetUserByAccessTokenResult | None:
    return await executor.query_single(
        """\
        with
            token := (
                select freeauth::Token
                filter
                    .access_token = <str>$access_token
                    and .is_revoked = false
            )
        select token { access_token, user };\
        """,
        access_token=access_token,
    )


async def get_user_by_account(
    executor: edgedb.AsyncIOExecutor,
    *,
    username: str | None,
    mobile: str | None,
    email: str | None,
) -> GetUserByAccountResult | None:
    return await executor.query_single(
        """\
        with
            username := <optional str>$username,
            mobile := <optional str>$mobile,
            email := <optional str>$email
        select
            freeauth::User { id, is_deleted }
        filter (
            .username ?= username if exists username else
            .mobile ?= mobile if exists mobile else
            .email ?= email if exists email else false
        )
        limit 1;\
        """,
        username=username,
        mobile=mobile,
        email=email,
    )


async def has_any_permission(
    executor: edgedb.AsyncIOExecutor,
    *,
    perm_codes: list[str],
) -> bool:
    return await executor.query_single(
        """\
        with
            module freeauth,
            perm_codes := str_upper(array_unpack(<array<str>>$perm_codes)),
            wildcard_perm := (
                select Permission
                filter
                    .application = global current_app
                    and .code = '*'
            ),
            user_perms := (
                select global current_user.permissions
                filter .application = global current_app
            )
        select any({
            any(user_perms.code_upper in perm_codes),
            wildcard_perm in user_perms
        });\
        """,
        perm_codes=perm_codes,
    )


async def send_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: FreeauthCodeType,
    verify_type: FreeauthVerifyType,
    code: str,
    ttl: int,
    max_attempts: int | None,
    attempts_ttl: int | None,
) -> SendCodeResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            account := <str>$account,
            code_type := <CodeType>$code_type,
            verify_type := <VerifyType>$verify_type,
            code := <str>$code,
            ttl := <int16>$ttl,
            max_attempts := <optional int64>$max_attempts,
            attempts_ttl := <optional int16>$attempts_ttl,
            sent_records := (
                select VerifyRecord
                filter (
                    exists max_attempts
                    and .account = account
                    and .code_type  = code_type
                    and .verify_type = verify_type
                    and .created_at >= (
                        datetime_of_transaction() -
                        cal::to_relative_duration(minutes := attempts_ttl)
                    )
                )
            ),
        for _ in (
            select true filter
                (count(sent_records) < max_attempts) ?? true
        ) union (
            select (
                insert VerifyRecord {
                    account := account,
                    code_type := code_type,
                    verify_type := verify_type,
                    code := code,
                    expired_at := (
                        datetime_of_transaction() +
                        cal::to_relative_duration(seconds := ttl)
                    )
                }
            ) {
                created_at,
                account,
                code_type,
                verify_type,
                expired_at,
                ttl := ttl
            }
        );\
        """,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
        ttl=ttl,
        max_attempts=max_attempts,
        attempts_ttl=attempts_ttl,
    )


async def sign_in(
    executor: edgedb.AsyncIOExecutor,
    *,
    client_info: str,
    id: uuid.UUID,
    access_token: str,
) -> SignInResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            user := (
                update User
                filter .id = <uuid>$id
                set { last_login_at := datetime_of_transaction() }
            ),
            token := (
                insert Token {
                    access_token := <str>$access_token,
                    user := user
                }
            ),
            audit_log := (
                insert AuditLog {
                    client_ip := client_info.client_ip,
                    event_type := AuditEventType.SignIn,
                    status_code := AuditStatusCode.OK,
                    raw_ua := <str>client_info.user_agent['raw_ua'],
                    os := <str>client_info.user_agent['os'],
                    device := <str>client_info.user_agent['device'],
                    browser := <str>client_info.user_agent['browser'],
                    user := user
                }
            )
        select user {
            name,
            username,
            email,
            mobile,
            org_type: { code, name },
            departments := (
                select .directly_organizations { code, name }
            ),
            roles: { code, name },
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        client_info=client_info,
        id=id,
        access_token=access_token,
    )


async def sign_out(
    executor: edgedb.AsyncIOExecutor,
    *,
    access_token: str,
) -> SignOutResult | None:
    return await executor.query_single(
        """\
        update freeauth::Token
        filter
            .access_token = <str>$access_token
            and .is_revoked = false
        set {
            revoked_at := datetime_of_transaction()
        };\
        """,
        access_token=access_token,
    )


async def sign_up(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str,
    email: str | None,
    mobile: str | None,
    hashed_password: str,
    reset_pwd_on_next_login: bool,
    client_info: str,
) -> SignInResult:
    return await executor.query_single(
        """\
        with
            module freeauth,
            name := <optional str>$name,
            username := <str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <str>$hashed_password,
            reset_pwd_on_next_login := <bool>$reset_pwd_on_next_login,
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            user := (
                insert User {
                    name := name,
                    username := username,
                    email := email,
                    mobile := mobile,
                    hashed_password := hashed_password,
                    reset_pwd_on_next_login := reset_pwd_on_next_login
                }
            ),
            audit_log := (
                insert AuditLog {
                    client_ip := client_info.client_ip,
                    event_type := AuditEventType.SignUp,
                    status_code := AuditStatusCode.OK,
                    raw_ua := <str>client_info.user_agent['raw_ua'],
                    os := <str>client_info.user_agent['os'],
                    device := <str>client_info.user_agent['device'],
                    browser := <str>client_info.user_agent['browser'],
                    user := user
                }
            )
        select user {
            name,
            username,
            email,
            mobile,
            org_type: { code, name },
            departments := (
                select .directly_organizations { code, name }
            ),
            roles: { code, name },
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        hashed_password=hashed_password,
        reset_pwd_on_next_login=reset_pwd_on_next_login,
        client_info=client_info,
    )


async def update_profile(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID,
    name: str,
    username: str,
    email: str | None,
    mobile: str | None,
) -> SignInResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            user := (
                update User
                filter
                    .id = <uuid>$id and not .is_deleted
                set {
                    name := <str>$name,
                    username := <str>$username,
                    email := <optional str>$email,
                    mobile := <optional str>$mobile
                }
            ),
        select user { 
            name,
            username,
            email,
            mobile,
            org_type: { code, name },
            departments := (
                select .directly_organizations { code, name }
            ),
            roles: { code, name },
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        id=id,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
    )


async def update_pwd(
    executor: edgedb.AsyncIOExecutor,
    *,
    client_info: str,
    id: uuid.UUID,
    hashed_password: str,
) -> GetUserByAccountResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            user := (
                update User
                filter
                    .id = <uuid>$id and not .is_deleted
                set {
                    hashed_password := <str>$hashed_password,
                    reset_pwd_on_next_login := false,
                }
            ),
            audit_log := (
                insert AuditLog {
                    client_ip := client_info.client_ip,
                    event_type := AuditEventType.ChangePwd,
                    status_code := AuditStatusCode.OK,
                    raw_ua := <str>client_info.user_agent['raw_ua'],
                    os := <str>client_info.user_agent['os'],
                    device := <str>client_info.user_agent['device'],
                    browser := <str>client_info.user_agent['browser'],
                    user := user
                }
            )
        select user { id, is_deleted };\
        """,
        client_info=client_info,
        id=id,
        hashed_password=hashed_password,
    )


async def upsert_login_setting(
    executor: edgedb.AsyncIOExecutor,
    *,
    configs: str,
) -> list[UpsertLoginSettingResult]:
    return await executor.query(
        """\
        for x in json_object_unpack(<json>$configs)
        union (
            insert freeauth::LoginSetting {
                key := x.0,
                value := to_str(x.1)
            } unless conflict on (.key) else (
                update freeauth::LoginSetting set { value := to_str(x.1)}
            )
        );\
        """,
        configs=configs,
    )


async def validate_account(
    executor: edgedb.AsyncIOExecutor,
    *,
    username: str | None,
    mobile: str | None,
    email: str | None,
    interval: int | None,
) -> ValidateAccountResult | None:
    return await executor.query_single(
        """\
        with
            module freeauth,
            username := <optional str>$username,
            mobile := <optional str>$mobile,
            email := <optional str>$email,
            interval := <optional int64>$interval,
            user := assert_single((
                select User
                filter
                    (exists username and .username ?= username) or
                    (exists mobile and .mobile ?= mobile) or
                    (exists email and .email ?= email)
            )),
            recent_success_attempt := (
                select AuditLog
                filter
                    .user = user
                    and .event_type = AuditEventType.SignIn
                    and .status_code = AuditStatusCode.OK
                    and .created_at >= (
                        datetime_of_statement() -
                        cal::to_relative_duration(minutes := interval)
                    )
                limit 1
            ),
            recent_failed_attempts := (
                select AuditLog
                filter
                    .user = user
                    and .event_type = AuditEventType.SignIn
                    and .status_code = AuditStatusCode.INVALID_PASSWORD
                    and (
                        .created_at >= recent_success_attempt.created_at
                        if exists recent_success_attempt else
                        .created_at >= (
                            datetime_of_statement() -
                            cal::to_relative_duration(minutes := interval)
                        )
                    )
            )
        select user {
            hashed_password,
            is_deleted,
            recent_failed_attempts := count(recent_failed_attempts)
        };\
        """,
        username=username,
        mobile=mobile,
        email=email,
        interval=interval,
    )


async def validate_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: FreeauthCodeType,
    verify_type: FreeauthVerifyType,
    code: str,
    max_attempts: int | None,
) -> ValidateCodeResult:
    return await executor.query_single(
        """\
        with
            module freeauth,
            account := <str>$account,
            code_type := <CodeType>$code_type,
            verify_type := <VerifyType>$verify_type,
            code := <str>$code,
            max_attempts := <optional int64>$max_attempts,
            consumable_record := (
                select VerifyRecord
                filter .account = account
                    and .code_type  = code_type
                    and .verify_type = verify_type
                    and .consumable
                    and (.incorrect_attempts <= max_attempts) ?? true
            ),
            record := ( select consumable_record filter .code = code ),
            valid_record := (
                update record
                filter .expired_at > datetime_of_transaction()
                set {
                    consumed_at := datetime_of_transaction()
                }
            ),
            incorrect_record := (
                update consumable_record
                filter exists max_attempts and not exists record
                set {
                    incorrect_attempts := .incorrect_attempts + 1,
                    expired_at := (
                        datetime_of_transaction() if
                        .incorrect_attempts = max_attempts - 1 else
                        .expired_at
                    )
                }
            ),
            code_attempts_exceeded := any(
                (incorrect_record.incorrect_attempts >= max_attempts) ?? false
            ),
            status_code := (
                AuditStatusCode.INVALID_CODE
                if not exists consumable_record
                else AuditStatusCode.CODE_ATTEMPTS_EXCEEDED
                if code_attempts_exceeded
                else AuditStatusCode.CODE_INCORRECT
                if not exists record
                else AuditStatusCode.CODE_EXPIRED
                if not exists valid_record
                else AuditStatusCode.OK
            )
        select (
            status_code := status_code,
        );\
        """,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
        max_attempts=max_attempts,
    )
