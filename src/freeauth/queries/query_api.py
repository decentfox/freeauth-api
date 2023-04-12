# AUTOGENERATED FROM:
#     'src/freeauth/queries/admin/create_user.edgeql'
#     'src/freeauth/queries/admin/delete_user.edgeql'
#     'src/freeauth/queries/admin/get_user_by_id.edgeql'
#     'src/freeauth/queries/admin/update_user.edgeql'
# WITH:
#     $ edgedb-py --file src/freeauth/queries/query_api.py


from __future__ import annotations

import dataclasses
import datetime
import uuid

import edgedb


class NoPydanticValidation:
    @classmethod
    def __get_validators__(cls):
        from pydantic.dataclasses import dataclass as pydantic_dataclass

        pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


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
    username: str | None


async def create_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str,
    username: str,
    email: str | None,
    mobile: str | None,
    hashed_password: str,
) -> CreateUserResult:
    return await executor.query_single(
        """\
        with
            name := <str>$name,
            username := <str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <str>$hashed_password
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
    id: uuid.UUID,
) -> list[DeleteUserResult]:
    return await executor.query(
        """\
        with
            user := (delete User filter .id = <uuid>$id)
        select
            User {id, username};\
        """,
        id=id,
    )


async def get_user_by_id(
    executor: edgedb.AsyncIOExecutor,
    *,
    id: uuid.UUID,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        select
            User {
                id, name, username, email, mobile,
                is_deleted, created_at, last_login_at
            }
        filter .id = <uuid>$id;\
        """,
        id=id,
    )


async def update_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None,
    username: str | None,
    email: str | None,
    mobile: str | None,
    hashed_password: str | None,
    id: uuid.UUID,
) -> CreateUserResult | None:
    return await executor.query_single(
        """\
        with
            name := <optional str>$name,
            username := <optional str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile,
            hashed_password := <optional str>$hashed_password
        select (
            update User filter .id = <uuid>$id
            set {
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
        id=id,
    )
