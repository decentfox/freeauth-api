# AUTOGENERATED FROM:
#     'src/freeauth/audit_logs/queries/create_audit_log.edgeql'
#     'src/freeauth/organizations/queries/create_department.edgeql'
#     'src/freeauth/organizations/queries/create_enterprise.edgeql'
#     'src/freeauth/organizations/queries/create_org_type.edgeql'
#     'src/freeauth/users/queries/create_user.edgeql'
#     'src/freeauth/organizations/queries/delete_org_type.edgeql'
#     'src/freeauth/organizations/queries/delete_organization.edgeql'
#     'src/freeauth/users/queries/delete_user.edgeql'
#     'src/freeauth/organizations/queries/get_department_by_id_or_code.edgeql'
#     'src/freeauth/organizations/queries/get_enterprise_by_id_or_code.edgeql'
#     'src/freeauth/settings/queries/get_login_setting.edgeql'
#     'src/freeauth/settings/queries/get_login_setting_by_key.edgeql'
#     'src/freeauth/organizations/queries/get_org_type_by_id_or_code.edgeql'
#     'src/freeauth/organizations/queries/get_organization_node.edgeql'
#     'src/freeauth/auth/queries/get_user_by_account.edgeql'
#     'src/freeauth/users/queries/get_user_by_id.edgeql'
#     'src/freeauth/organizations/queries/organization_add_member.edgeql'
#     'src/freeauth/organizations/queries/query_org_types.edgeql'
#     'src/freeauth/auth/queries/send_code.edgeql'
#     'src/freeauth/auth/queries/sign_in.edgeql'
#     'src/freeauth/auth/queries/sign_up.edgeql'
#     'src/freeauth/organizations/queries/update_department.edgeql'
#     'src/freeauth/organizations/queries/update_enterprise.edgeql'
#     'src/freeauth/organizations/queries/update_org_type.edgeql'
#     'src/freeauth/organizations/queries/update_org_type_status.edgeql'
#     'src/freeauth/users/queries/update_user.edgeql'
#     'src/freeauth/users/queries/update_user_status.edgeql'
#     'src/freeauth/settings/queries/upsert_login_setting.edgeql'
#     'src/freeauth/auth/queries/validate_code.edgeql'
# WITH:
#     $ edgedb-py --file src/freeauth/query_api.py


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


class AuthAuditEventType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNOUT = "SignOut"
    SIGNUP = "SignUp"


class AuthCodeType(enum.Enum):
    SMS = "SMS"
    EMAIL = "Email"


class AuthVerifyType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNUP = "SignUp"


@dataclasses.dataclass
class CreateAuditLogResult(NoPydanticValidation):
    id: uuid.UUID
    client_ip: str
    os: str | None
    device: str | None
    browser: str | None
    status_code: int
    is_succeed: bool
    event_type: AuthAuditEventType
    created_at: datetime.datetime
    user: CreateAuditLogResultUser


@dataclasses.dataclass
class CreateAuditLogResultUser(NoPydanticValidation):
    id: uuid.UUID
    username: str | None
    mobile: str | None
    email: str | None


@dataclasses.dataclass
class CreateDepartmentResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None
    description: str | None
    parent: CreateDepartmentResultParent
    enterprise: CreateDepartmentResultEnterprise


@dataclasses.dataclass
class CreateDepartmentResultEnterprise(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None


@dataclasses.dataclass
class CreateDepartmentResultParent(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None


@dataclasses.dataclass
class CreateEnterpriseResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None
    tax_id: str | None
    issuing_bank: str | None
    bank_account_number: str | None
    contact_address: str | None
    contact_phone_num: str | None


@dataclasses.dataclass
class CreateOrgTypeResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str
    description: str | None
    is_deleted: bool
    is_protected: bool


@dataclasses.dataclass
class CreateUserResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    username: str | None
    email: str | None
    mobile: str | None
    departments: list[CreateUserResultDepartmentsItem]
    is_deleted: bool
    created_at: datetime.datetime
    last_login_at: datetime.datetime | None


@dataclasses.dataclass
class CreateUserResultDepartmentsItem(NoPydanticValidation):
    id: uuid.UUID
    code: str | None
    name: str


@dataclasses.dataclass
class DeleteOrgTypeResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str


@dataclasses.dataclass
class DeleteOrganizationResult(NoPydanticValidation):
    id: uuid.UUID


@dataclasses.dataclass
class DeleteUserResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None


@dataclasses.dataclass
class GetLoginSettingResult(NoPydanticValidation):
    id: uuid.UUID
    key: str
    value: str


@dataclasses.dataclass
class GetOrganizationNodeResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str | None
    description: str | None
    has_children: bool


@dataclasses.dataclass
class GetUserByAccountResult(NoPydanticValidation):
    id: uuid.UUID
    hashed_password: str | None
    is_deleted: bool


@dataclasses.dataclass
class SendCodeResult(NoPydanticValidation):
    id: uuid.UUID
    created_at: datetime.datetime
    account: str
    code_type: AuthCodeType
    verify_type: AuthVerifyType
    expired_at: datetime.datetime
    ttl: int


@dataclasses.dataclass
class SignInResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    username: str | None
    email: str | None
    mobile: str | None
    is_deleted: bool
    created_at: datetime.datetime
    last_login_at: datetime.datetime | None


@dataclasses.dataclass
class UpdateOrgTypeStatusResult(NoPydanticValidation):
    id: uuid.UUID
    name: str
    code: str
    is_deleted: bool


@dataclasses.dataclass
class UpdateUserStatusResult(NoPydanticValidation):
    id: uuid.UUID
    name: str | None
    is_deleted: bool


class ValidateCodeResult(typing.NamedTuple):
    code_required: bool
    code_found: bool
    code_valid: bool
    incorrect_attempts: int


async def create_audit_log(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_id: uuid.UUID,
    client_info: str,
    event_type: AuthAuditEventType,
    status_code: int,
) -> CreateAuditLogResult:
    return await executor.query_single(
        """\
        WITH
            user := (SELECT User FILTER .id = <uuid>$user_id),
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            )
        SELECT (
            INSERT auth::AuditLog {
                client_ip := <str>client_info.client_ip,
                event_type := <auth::AuditEventType>$event_type,
                status_code := <int16>$status_code,
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
        event_type=event_type,
        status_code=status_code,
    )


async def create_department(
    executor: edgedb.AsyncIOExecutor,
    *,
    parent_id: uuid.UUID,
    name: str,
    code: str | None,
    description: str | None,
) -> CreateDepartmentResult | None:
    return await executor.query_single(
        """\
        WITH
            parent := (
                SELECT Organization FILTER .id = <uuid>$parent_id
            ),
            parent_is_enterprise := EXISTS parent[is Enterprise],
            enterprise := assert_single((
                SELECT Enterprise FILTER (
                    .id = parent[is Enterprise].id IF parent_is_enterprise ELSE
                    .id = parent[is Department].enterprise.id
                )
            ))
        FOR _ IN (
            SELECT true FILTER EXISTS parent
        ) UNION (
            SELECT (
                INSERT Department {
                    name := <str>$name,
                    code := <optional str>$code,
                    description := <optional str>$description,
                    enterprise := enterprise,
                    parent := parent
                }
            ) {
                name,
                code,
                description,
                parent: {
                    name,
                    code
                },
                enterprise: {
                    name,
                    code,
                }
            }
        );\
        """,
        parent_id=parent_id,
        name=name,
        code=code,
        description=description,
    )


async def create_enterprise(
    executor: edgedb.AsyncIOExecutor,
    *,
    org_type_id: uuid.UUID,
    name: str,
    code: str | None,
    tax_id: str | None,
    issuing_bank: str | None,
    bank_account_number: str | None,
    contact_address: str | None,
    contact_phone_num: str | None,
) -> CreateEnterpriseResult | None:
    return await executor.query_single(
        """\
        WITH
            org_type := (
                SELECT OrganizationType FILTER .id = <uuid>$org_type_id
            )
        FOR _ IN (
            SELECT true FILTER EXISTS org_type
        ) UNION (
            SELECT (
                INSERT Enterprise {
                    name := <str>$name,
                    code := <optional str>$code,
                    tax_id := <optional str>$tax_id,
                    issuing_bank := <optional str>$issuing_bank,
                    bank_account_number := <optional str>$bank_account_number,
                    contact_address := <optional str>$contact_address,
                    contact_phone_num := <optional str>$contact_phone_num,
                    org_type := org_type
                }
            ) {
                name,
                code,
                tax_id,
                issuing_bank,
                bank_account_number,
                contact_address,
                contact_phone_num
            }
        );\
        """,
        org_type_id=org_type_id,
        name=name,
        code=code,
        tax_id=tax_id,
        issuing_bank=issuing_bank,
        bank_account_number=bank_account_number,
        contact_address=contact_address,
        contact_phone_num=contact_phone_num,
    )


async def create_org_type(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str,
    code: str,
    description: str | None,
) -> CreateOrgTypeResult:
    return await executor.query_single(
        """\
        WITH
            name := <str>$name,
            code := <str>$code,
            description := <optional str>$description
        SELECT (
            INSERT OrganizationType {
                name := name,
                code := code,
                description := description
            }
        ) { name, code, description, is_deleted, is_protected };\
        """,
        name=name,
        code=code,
        description=description,
    )


async def create_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str | None,
    email: str | None,
    mobile: str | None,
    hashed_password: str | None,
    organization_ids: list[uuid.UUID] | None,
) -> CreateUserResult:
    return await executor.query_single(
        """\
        with
            name := <optional str>$name,
            username := <optional str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <optional str>$hashed_password,
            organization_ids := <optional array<uuid>>$organization_ids
        select (
            insert User {
                name := name,
                username := username,
                email := email,
                mobile := mobile,
                hashed_password := hashed_password,
                org_branches := (
                    SELECT Organization
                    FILTER .id IN array_unpack(
                        organization_ids ?? <array<uuid>>[]
                    )
                )
            }
        ) {
            name,
            username,
            email,
            mobile,
            departments := (
                SELECT .org_branches { code, name }
            ),
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
        organization_ids=organization_ids,
    )


async def delete_org_type(
    executor: edgedb.AsyncIOExecutor,
    *,
    ids: list[uuid.UUID],
) -> list[DeleteOrgTypeResult]:
    return await executor.query(
        """\
        SELECT (
            DELETE OrganizationType
            FILTER .id in array_unpack(<array<uuid>>$ids) AND NOT .is_protected
        ) { name, code };\
        """,
        ids=ids,
    )


async def delete_organization(
    executor: edgedb.AsyncIOExecutor,
    *,
    ids: list[uuid.UUID],
) -> list[DeleteOrganizationResult]:
    return await executor.query(
        """\
        DELETE Organization FILTER .id in array_unpack(<array<uuid>>$ids);\
        """,
        ids=ids,
    )


async def delete_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_ids: list[uuid.UUID],
) -> list[DeleteUserResult]:
    return await executor.query(
        """\
        SELECT (
            DELETE User FILTER .id in array_unpack(<array<uuid>>$user_ids)
        ) { name } ORDER BY .created_at DESC;\
        """,
        user_ids=user_ids,
    )


async def get_department_by_id_or_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    code: str | None,
    enterprise_id: uuid.UUID | None,
) -> CreateDepartmentResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            code := <optional str>$code,
            enterprise_id := <optional uuid>$enterprise_id
        SELECT assert_single(
            (
                SELECT Department {
                    name,
                    code,
                    description,
                    parent: {
                        name,
                        code
                    },
                    enterprise: {
                        name,
                        code,
                    }
                }
                FILTER (
                    .id = id IF EXISTS id ELSE (
                        .code ?= code AND
                        .enterprise.id = enterprise_id
                    ) IF EXISTS enterprise_id ELSE false
                )
            )
        );\
        """,
        id=id,
        code=code,
        enterprise_id=enterprise_id,
    )


async def get_enterprise_by_id_or_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    code: str | None,
    org_type_id: uuid.UUID | None,
    org_type_code: str | None,
) -> CreateEnterpriseResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            code := <optional str>$code,
            org_type_id := <optional uuid>$org_type_id,
            org_type_code := <optional str>$org_type_code
        SELECT assert_single(
            (
                SELECT Enterprise {
                    name,
                    code,
                    tax_id,
                    issuing_bank,
                    bank_account_number,
                    contact_address,
                    contact_phone_num
                }
                FILTER (
                    .id = id IF EXISTS id ELSE (
                        .code ?= code AND
                        .org_type.id = org_type_id
                    ) IF EXISTS org_type_id ELSE (
                        .code ?= code AND
                        .org_type.code = org_type_code
                    )
                )
            )
        );\
        """,
        id=id,
        code=code,
        org_type_id=org_type_id,
        org_type_code=org_type_code,
    )


async def get_login_setting(
    executor: edgedb.AsyncIOExecutor,
) -> list[GetLoginSettingResult]:
    return await executor.query(
        """\
        SELECT LoginSetting { key, value } ORDER BY .key;\
        """,
    )


async def get_login_setting_by_key(
    executor: edgedb.AsyncIOExecutor,
    *,
    key: str,
) -> GetLoginSettingResult | None:
    return await executor.query_single(
        """\
        SELECT LoginSetting { key, value } FILTER .key = <str>$key;\
        """,
        key=key,
    )


async def get_org_type_by_id_or_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    code: str | None,
) -> CreateOrgTypeResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            code := <optional str>$code
        SELECT assert_single(
            (
                SELECT OrganizationType {
                    name,
                    code,
                    description,
                    is_deleted,
                    is_protected
                }
                FILTER .id = id IF EXISTS id ELSE .code = code
            )
        );\
        """,
        id=id,
        code=code,
    )


async def get_organization_node(
    executor: edgedb.AsyncIOExecutor,
    *,
    org_type_id: uuid.UUID | None,
    org_type_code: str | None,
    parent_id: uuid.UUID | None,
) -> list[GetOrganizationNodeResult]:
    return await executor.query(
        """\
        WITH
            ot_id := <optional uuid>$org_type_id,
            ot_code := <optional str>$org_type_code,
            parent_id := <optional uuid>$parent_id
        SELECT
            Organization {
                name,
                code,
                [IS Department].description,
                has_children := EXISTS .children
            }
        FILTER (
            [IS Department].parent.id = parent_id IF EXISTS parent_id ELSE
            [IS Enterprise].org_type.id = ot_id IF EXISTS ot_id ELSE
            [IS Enterprise].org_type.code = ot_code
        )
        ORDER BY .created_at;\
        """,
        org_type_id=org_type_id,
        org_type_code=org_type_code,
        parent_id=parent_id,
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
        WITH
            username := <optional str>$username,
            mobile := <optional str>$mobile,
            email := <optional str>$email
        SELECT
            User { id, hashed_password, is_deleted }
        FILTER (
            .username ?= username IF EXISTS username ELSE
            .mobile ?= mobile IF EXISTS mobile ELSE
            .email ?= email IF EXISTS email ELSE false
        )
        LIMIT 1;\
        """,
        username=username,
        mobile=mobile,
        email=email,
    )


async def get_user_by_id(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        SELECT
            User {
                name,
                username,
                email,
                mobile,
                departments := (
                    SELECT .org_branches { code, name }
                ),
                is_deleted,
                created_at,
                last_login_at
            }
        FILTER .id = <uuid>$id;\
        """,
        id=id,
    )


async def organization_add_member(
    executor: edgedb.AsyncIOExecutor,
    *,
    user_ids: list[uuid.UUID],
    organization_ids: list[uuid.UUID],
) -> list[CreateUserResult]:
    return await executor.query(
        """\
        WITH
            user_ids := <array<uuid>>$user_ids,
            organization_ids := <array<uuid>>$organization_ids
        SELECT (
            UPDATE User FILTER .id in array_unpack(user_ids)
            SET {
                org_branches += (
                    SELECT Organization
                    FILTER .id IN array_unpack(organization_ids)
                )
            }
        ) {
            name,
            username,
            email,
            mobile,
            departments := (
                SELECT .org_branches { code, name }
            ),
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        user_ids=user_ids,
        organization_ids=organization_ids,
    )


async def query_org_types(
    executor: edgedb.AsyncIOExecutor,
) -> list[CreateOrgTypeResult]:
    return await executor.query(
        """\
        SELECT OrganizationType {
            name, code, description, is_deleted, is_protected
        } ORDER BY
            .is_deleted THEN
            .is_protected DESC THEN
            .code;\
        """,
    )


async def send_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: AuthCodeType,
    verify_type: AuthVerifyType,
    code: str,
    ttl: int,
    max_attempts: int | None,
    attempts_ttl: int | None,
) -> SendCodeResult | None:
    return await executor.query_single(
        """\
        WITH
            account := <str>$account,
            code_type := <auth::CodeType>$code_type,
            verify_type := <auth::VerifyType>$verify_type,
            code := <str>$code,
            ttl := <int16>$ttl,
            max_attempts := <optional int64>$max_attempts,
            attempts_ttl := <optional int16>$attempts_ttl,
            sent_records := (
                SELECT auth::VerifyRecord
                FILTER (
                    EXISTS max_attempts
                    AND EXISTS attempts_ttl
                    AND EXISTS attempts_ttl
                    AND .account = account
                    AND .code_type  = code_type
                    AND .verify_type = verify_type
                    AND .created_at >= (
                        datetime_of_transaction() -
                        <cal::relative_duration>(
                            <str>attempts_ttl ++ ' minutes'
                        )
                    )
                )
            ),
        FOR _ IN (
            SELECT true FILTER (
                true IF NOT EXISTS max_attempts ELSE
                count(sent_records) < max_attempts
            )
        ) UNION (
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
        WITH
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            user := (
                UPDATE User
                FILTER .id = <uuid>$id
                SET { last_login_at := datetime_of_transaction() }
            ),
            token := (
                INSERT auth::Token {
                    access_token := <str>$access_token,
                    user := user
                }
            ),
            audit_log := (
                INSERT auth::AuditLog {
                    client_ip := <str>client_info.client_ip,
                    event_type := <auth::AuditEventType>'SignIn',
                    status_code := <int16>200,
                    raw_ua := <str>client_info.user_agent['raw_ua'],
                    os := <str>client_info.user_agent['os'],
                    device := <str>client_info.user_agent['device'],
                    browser := <str>client_info.user_agent['browser'],
                    user := user
                }
            )
        SELECT user {
            name,
            username,
            email,
            mobile,
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        client_info=client_info,
        id=id,
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
    client_info: str,
) -> SignInResult:
    return await executor.query_single(
        """\
        WITH
            name := <optional str>$name,
            username := <str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <str>$hashed_password,
            client_info := (
                <tuple<client_ip: str, user_agent: json>><json>$client_info
            ),
            user := (
                INSERT User {
                    name := name,
                    username := username,
                    email := email,
                    mobile := mobile,
                    hashed_password := hashed_password
                }
            ),
            audit_log := (
                INSERT auth::AuditLog {
                    client_ip := <str>client_info.client_ip,
                    event_type := <auth::AuditEventType>'SignUp',
                    status_code := <int16>200,
                    raw_ua := <str>client_info.user_agent['raw_ua'],
                    os := <str>client_info.user_agent['os'],
                    device := <str>client_info.user_agent['device'],
                    browser := <str>client_info.user_agent['browser'],
                    user := user
                }
            )
        SELECT user {
            name,
            username,
            email,
            mobile,
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
        client_info=client_info,
    )


async def update_department(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    current_code: str | None,
    enterprise_id: uuid.UUID | None,
    parent_id: uuid.UUID,
    name: str,
    code: str | None,
    description: str | None,
) -> CreateDepartmentResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            current_code := <optional str>$current_code,
            enterprise_id := <optional uuid>$enterprise_id,
            parent := (
                SELECT Organization FILTER .id = <uuid>$parent_id
            ),
            parent_is_enterprise := EXISTS parent[is Enterprise],
            enterprise := assert_single((
                SELECT Enterprise FILTER (
                    .id = parent[is Enterprise].id IF parent_is_enterprise ELSE
                    .id = parent[is Department].enterprise.id
                )
            )),
            department := assert_single((
                SELECT Department
                FILTER (
                    .id = id IF EXISTS id ELSE (
                        .code ?= current_code AND
                        .enterprise.id = enterprise_id
                    ) IF EXISTS enterprise_id ELSE false
                )
            ))
        SELECT (
            UPDATE department
            SET {
                name := <str>$name,
                code := <optional str>$code,
                description := <optional str>$description,
                enterprise := enterprise,
                parent := parent
            }
        ) {
            name,
            code,
            description,
            parent: {
                name,
                code
            },
            enterprise: {
                name,
                code,
            }
        };\
        """,
        id=id,
        current_code=current_code,
        enterprise_id=enterprise_id,
        parent_id=parent_id,
        name=name,
        code=code,
        description=description,
    )


async def update_enterprise(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    current_code: str | None,
    org_type_id: uuid.UUID | None,
    org_type_code: str | None,
    name: str,
    code: str | None,
    tax_id: str | None,
    issuing_bank: str | None,
    bank_account_number: str | None,
    contact_address: str | None,
    contact_phone_num: str | None,
) -> CreateEnterpriseResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            current_code := <optional str>$current_code,
            org_type_id := <optional uuid>$org_type_id,
            org_type_code := <optional str>$org_type_code,
            enterprise := assert_single((
                SELECT Enterprise
                FILTER (
                    .id = id IF EXISTS id ELSE (
                        .code ?= current_code AND
                        .org_type.id = org_type_id
                    ) IF EXISTS org_type_id ELSE (
                        .code ?= current_code AND
                        .org_type.code = org_type_code
                    )
                )
            ))
        SELECT (
            UPDATE enterprise
            SET {
                name := <str>$name,
                code := <optional str>$code,
                tax_id := <optional str>$tax_id,
                issuing_bank := <optional str>$issuing_bank,
                bank_account_number := <optional str>$bank_account_number,
                contact_address := <optional str>$contact_address,
                contact_phone_num := <optional str>$contact_phone_num,
            }
        ) {
            name,
            code,
            tax_id,
            issuing_bank,
            bank_account_number,
            contact_address,
            contact_phone_num
        };\
        """,
        id=id,
        current_code=current_code,
        org_type_id=org_type_id,
        org_type_code=org_type_code,
        name=name,
        code=code,
        tax_id=tax_id,
        issuing_bank=issuing_bank,
        bank_account_number=bank_account_number,
        contact_address=contact_address,
        contact_phone_num=contact_phone_num,
    )


async def update_org_type(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID | None,
    current_code: str | None,
    name: str | None,
    code: str | None,
    description: str | None,
    is_deleted: bool | None,
) -> CreateOrgTypeResult | None:
    return await executor.query_single(
        """\
        WITH
            id := <optional uuid>$id,
            current_code := <optional str>$current_code,
            name := <optional str>$name,
            code := <optional str>$code,
            description := <optional str>$description,
            is_deleted := <optional bool>$is_deleted,
            org_type := assert_single((
                SELECT OrganizationType
                FILTER .id = id IF EXISTS id ELSE .code = code
            ))
        SELECT (
            UPDATE org_type
            SET {
                name := name ?? .name,
                code := code ?? .code,
                description := description ?? .description,
                deleted_at := (
                    .deleted_at IF NOT EXISTS is_deleted ELSE
                    datetime_of_transaction()
                    IF is_deleted AND NOT .is_protected ELSE {}
                )
            }
        ) { name, code, description, is_deleted, is_protected };\
        """,
        id=id,
        current_code=current_code,
        name=name,
        code=code,
        description=description,
        is_deleted=is_deleted,
    )


async def update_org_type_status(
    executor: edgedb.AsyncIOExecutor,
    *,
    is_deleted: bool,
    ids: list[uuid.UUID],
) -> list[UpdateOrgTypeStatusResult]:
    return await executor.query(
        """\
        WITH
            is_deleted := <bool>$is_deleted
        SELECT (
            UPDATE OrganizationType
            FILTER .id in array_unpack(<array<uuid>>$ids) AND NOT .is_protected
            SET {
                deleted_at := datetime_of_transaction() IF is_deleted ELSE {}
            }
        ) { name, code, is_deleted };\
        """,
        is_deleted=is_deleted,
        ids=ids,
    )


async def update_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str | None,
    email: str | None,
    mobile: str | None,
    organization_ids: list[uuid.UUID] | None,
    id: uuid.UUID,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        WITH
            name := <optional str>$name,
            username := <optional str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            organization_ids := <optional array<uuid>>$organization_ids
        SELECT (
            UPDATE User FILTER .id = <uuid>$id
            SET {
                name := name,
                username := username,
                email := email,
                mobile := mobile,
                org_branches := (
                    SELECT Organization
                    FILTER .id IN array_unpack(
                        organization_ids ?? <array<uuid>>[]
                    )
                )
            }
        ) {
            name,
            username,
            email,
            mobile,
            departments := (
                SELECT .org_branches { code, name }
            ),
            is_deleted,
            created_at,
            last_login_at
        };\
        """,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        organization_ids=organization_ids,
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
        WITH
            user_ids := <array<uuid>>$user_ids,
            is_deleted := <bool>$is_deleted
        SELECT (
            UPDATE User FILTER .id in array_unpack(user_ids)
            SET {
                deleted_at := datetime_of_transaction() if is_deleted else {}
            }
        ) {
            name,
            is_deleted
        } ORDER BY .created_at DESC;\
        """,
        user_ids=user_ids,
        is_deleted=is_deleted,
    )


async def upsert_login_setting(
    executor: edgedb.AsyncIOExecutor,
    *,
    key: str,
    value: str,
) -> GetLoginSettingResult:
    return await executor.query_single(
        """\
        WITH
            key := <str>$key,
            value := <str>$value
        SELECT (
            INSERT LoginSetting {
                key := key,
                value := value
            } UNLESS CONFLICT ON (.key) ELSE (
                UPDATE LoginSetting SET { value := value}
            )
        ) { key, value };\
        """,
        key=key,
        value=value,
    )


async def validate_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    account: str,
    code_type: AuthCodeType,
    verify_type: AuthVerifyType,
    code: str,
    max_attempts: int | None,
) -> ValidateCodeResult:
    return await executor.query_single(
        """\
        WITH
            account := <str>$account,
            code_type := <auth::CodeType>$code_type,
            verify_type := <auth::VerifyType>$verify_type,
            code := <str>$code,
            max_attempts := <optional int64>$max_attempts,
            consumable_record := (
                SELECT auth::VerifyRecord
                FILTER .account = account
                    AND .code_type  = code_type
                    AND .verify_type = verify_type
                    AND .consumable
                    AND (
                        true IF NOT EXISTS max_attempts ELSE
                        .incorrect_attempts <= max_attempts
                    )
                ORDER BY .created_at DESC
                LIMIT 1
            ),
            record := (SELECT consumable_record FILTER .code = code),
            valid_record := (
                UPDATE record
                FILTER .expired_at > datetime_of_transaction()
                SET {
                    consumed_at := datetime_of_transaction()
                }
            ),
            incorrect_record := (
                UPDATE consumable_record
                FILTER EXISTS max_attempts AND NOT EXISTS record
                SET {
                    incorrect_attempts := .incorrect_attempts + 1,
                    expired_at := (
                        datetime_of_transaction() IF
                        .incorrect_attempts = max_attempts - 1 ELSE
                        .expired_at
                    )
                }
            )
        SELECT (
            code_required := NOT EXISTS consumable_record,
            code_found := EXISTS record,
            code_valid := EXISTS valid_record,
            incorrect_attempts := (
                incorrect_record.incorrect_attempts ??
                consumable_record.incorrect_attempts ?? 0
            )
        );\
        """,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
        max_attempts=max_attempts,
    )
